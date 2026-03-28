import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:receive_sharing_intent/receive_sharing_intent.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() => runApp(const NostromoRemoteApp());

class NostromoRemoteApp extends StatelessWidget {
  const NostromoRemoteApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Nostromo Remote',
      theme: ThemeData.dark().copyWith(
        colorScheme: ColorScheme.dark(
          primary: const Color(0xFF33FF00),
          secondary: const Color(0xFF33FF00),
          surface: const Color(0xFF0A0A0A),
        ),
        scaffoldBackgroundColor: const Color(0xFF0A0A0A),
      ),
      home: const HomePage(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _hostController = TextEditingController();
  String _status = 'STANDBY';
  String _lastSent = '';
  bool _connected = false;
  StreamSubscription? _shareSub;
  Timer? _pollTimer;
  static const _port = 8080;
  static const _prefKey = 'nostromo_host';
  static const _green = Color(0xFF33FF00);
  static const _dim = Color(0xFF146400);

  // Player state
  bool _playing = false;
  bool _paused = false;
  double _position = 0;
  double _duration = 0;
  int _volume = 100;
  bool _muted = false;

  @override
  void initState() {
    super.initState();
    _loadHost();
    _listenShare();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _shareSub?.cancel();
    _hostController.dispose();
    super.dispose();
  }

  // ─── Settings ──────────────────────────────────────────────

  Future<void> _loadHost() async {
    final prefs = await SharedPreferences.getInstance();
    final host = prefs.getString(_prefKey) ?? '';
    _hostController.text = host;
    if (host.isNotEmpty) _ping();
  }

  Future<void> _saveHost() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKey, _hostController.text.trim());
    _ping();
  }

  // ─── Network ───────────────────────────────────────────────

  String get _baseUrl => 'http://${_hostController.text.trim()}:$_port';

  Future<void> _ping() async {
    final host = _hostController.text.trim();
    if (host.isEmpty) return;

    setState(() => _status = 'CONNECTING...');
    try {
      final resp = await http
          .get(Uri.parse('$_baseUrl/ping'))
          .timeout(const Duration(seconds: 3));
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        setState(() {
          _connected = true;
          _status = 'LINK TO ${data['name'] ?? 'NOSTROMO'} ESTABLISHED';
        });
        _startPolling();
      } else {
        setState(() {
          _connected = false;
          _status = 'ERROR: ${resp.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _connected = false;
        _status = 'NO SIGNAL';
      });
    }
  }

  Future<void> _sendUrl(String url) async {
    final host = _hostController.text.trim();
    if (host.isEmpty) {
      _showSnack('SET NOSTROMO ADDRESS FIRST');
      return;
    }

    setState(() => _status = 'TRANSMITTING...');
    try {
      final resp = await http
          .post(
            Uri.parse('$_baseUrl/play'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'url': url}),
          )
          .timeout(const Duration(seconds: 5));

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        setState(() {
          _status = 'TRANSMITTED: ${data['video_id'] ?? 'OK'}';
          _lastSent = url;
        });
        _showSnack('SENT TO NOSTROMO');
      } else {
        final data = jsonDecode(resp.body);
        setState(() => _status = 'ERROR: ${data['error'] ?? resp.statusCode}');
        _showSnack('SEND FAILED');
      }
    } catch (e) {
      setState(() => _status = 'TRANSMISSION FAILED');
      _showSnack('NO CONNECTION TO NOSTROMO');
    }
  }

  // ─── Player remote control ─────────────────────────────────

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 2), (_) => _fetchStatus());
  }

  void _stopPolling() {
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  Future<void> _fetchStatus() async {
    final host = _hostController.text.trim();
    if (host.isEmpty) return;
    try {
      final resp = await http
          .get(Uri.parse('$_baseUrl/status'))
          .timeout(const Duration(seconds: 2));
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        setState(() {
          _playing = data['playing'] ?? false;
          _paused = data['paused'] ?? false;
          _position = (data['position'] ?? 0).toDouble();
          _duration = (data['duration'] ?? 0).toDouble();
          _volume = data['volume'] ?? 100;
          _muted = data['muted'] ?? false;
        });
      }
    } catch (_) {}
  }

  Future<void> _postCommand(String endpoint, Map<String, dynamic> body) async {
    final host = _hostController.text.trim();
    if (host.isEmpty) return;
    try {
      await http
          .post(
            Uri.parse('$_baseUrl$endpoint'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 3));
      _fetchStatus();
    } catch (_) {}
  }

  void _seek(double seconds) => _postCommand('/seek', {'seconds': seconds});
  void _volumeChange(double delta) => _postCommand('/volume', {'delta': delta});
  void _togglePause() => _postCommand('/pause', {});

  String _fmtTime(double seconds) {
    final m = seconds ~/ 60;
    final s = (seconds % 60).toInt();
    return '$m:${s.toString().padLeft(2, '0')}';
  }

  // ─── Share intent ──────────────────────────────────────────

  void _listenShare() {
    // Handle share when app is already running
    _shareSub = ReceiveSharingIntent.instance.getMediaStream().listen(
      (List<SharedMediaFile> files) {
        _handleShared(files);
      },
    );

    // Handle share that launched the app
    ReceiveSharingIntent.instance.getInitialMedia().then((files) {
      _handleShared(files);
    });
  }

  void _handleShared(List<SharedMediaFile> files) {
    for (final file in files) {
      final text = file.path; // For text shares, path contains the text
      if (text.contains('youtube.com') || text.contains('youtu.be')) {
        _sendUrl(text);
        return;
      }
    }
  }

  // ─── UI helpers ────────────────────────────────────────────

  void _showSnack(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg, style: const TextStyle(color: _green, fontFamily: 'monospace')),
        backgroundColor: Colors.black,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  Widget _controlBtn(IconData icon, VoidCallback onPressed, {double size = 36}) {
    return IconButton(
      icon: Icon(icon, color: _green, size: size),
      onPressed: onPressed,
      splashRadius: size * 0.6,
    );
  }

  // ─── Build ─────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 20),
              // Title
              const Text(
                'NOSTROMO REMOTE',
                style: TextStyle(
                  color: _green,
                  fontSize: 24,
                  fontFamily: 'monospace',
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'WEYLAND-YUTANI CORP.',
                style: TextStyle(color: _dim, fontSize: 12, fontFamily: 'monospace'),
              ),
              const SizedBox(height: 40),

              // Host input
              const Text(
                'NOSTROMO ADDRESS:',
                style: TextStyle(color: _dim, fontSize: 12, fontFamily: 'monospace'),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _hostController,
                      style: const TextStyle(color: _green, fontFamily: 'monospace'),
                      decoration: InputDecoration(
                        hintText: 'palm.local or 192.168.1.x',
                        hintStyle: const TextStyle(color: _dim),
                        enabledBorder: const OutlineInputBorder(
                          borderSide: BorderSide(color: _dim),
                        ),
                        focusedBorder: const OutlineInputBorder(
                          borderSide: BorderSide(color: _green),
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 8,
                        ),
                      ),
                      onSubmitted: (_) => _saveHost(),
                    ),
                  ),
                  const SizedBox(width: 12),
                  ElevatedButton(
                    onPressed: _saveHost,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _dim,
                      foregroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 12,
                      ),
                    ),
                    child: const Text('LINK', style: TextStyle(fontFamily: 'monospace')),
                  ),
                ],
              ),

              const SizedBox(height: 40),

              // Status
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  border: Border.all(color: _connected ? _green : _dim),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          _connected ? Icons.link : Icons.link_off,
                          color: _connected ? _green : _dim,
                          size: 16,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          _status,
                          style: TextStyle(
                            color: _connected ? _green : _dim,
                            fontFamily: 'monospace',
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                    if (_lastSent.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(
                        'LAST: ${_lastSent.length > 40 ? '${_lastSent.substring(0, 40)}...' : _lastSent}',
                        style: const TextStyle(
                          color: _dim,
                          fontFamily: 'monospace',
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ],
                ),
              ),

              const SizedBox(height: 32),

              // Remote control
              if (_connected && _playing) ...[
                // Progress
                Text(
                  '${_fmtTime(_position)} / ${_fmtTime(_duration)}',
                  style: const TextStyle(color: _green, fontSize: 14, fontFamily: 'monospace'),
                ),
                const SizedBox(height: 8),
                if (_duration > 0)
                  LinearProgressIndicator(
                    value: _position / _duration,
                    backgroundColor: _dim.withAlpha(80),
                    valueColor: const AlwaysStoppedAnimation<Color>(_green),
                    minHeight: 3,
                  ),
                const SizedBox(height: 24),

                // Seek + Pause row
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _controlBtn(Icons.replay_10, () => _seek(-10)),
                    const SizedBox(width: 24),
                    _controlBtn(
                      _paused ? Icons.play_arrow : Icons.pause,
                      _togglePause,
                      size: 48,
                    ),
                    const SizedBox(width: 24),
                    _controlBtn(Icons.forward_10, () => _seek(10)),
                  ],
                ),
                const SizedBox(height: 24),

                // Volume row
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _controlBtn(Icons.volume_down, () => _volumeChange(-0.1)),
                    const SizedBox(width: 16),
                    Text(
                      _muted ? 'MUTE' : 'VOL $_volume%',
                      style: const TextStyle(color: _dim, fontSize: 14, fontFamily: 'monospace'),
                    ),
                    const SizedBox(width: 16),
                    _controlBtn(Icons.volume_up, () => _volumeChange(0.1)),
                  ],
                ),
              ],

              const Spacer(),

              // Instructions
              Text(
                _connected && _playing
                    ? 'NOW PLAYING ON NOSTROMO'
                    : 'SHARE A YOUTUBE VIDEO FROM THE\nYOUTUBE APP TO SEND IT TO NOSTROMO.',
                style: const TextStyle(color: _dim, fontSize: 12, fontFamily: 'monospace'),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}

