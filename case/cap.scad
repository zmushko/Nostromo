// ============================================
// NOSTROMO — Cap / Lid
// ============================================
// Sits on top of the case body (nostromo.scad)
// Print as-is (flat bottom on bed, rounded top up)
// No lip — held by M3 screws only
//
// Cap is 5mm thick for rigidity.
// Pockets (2mm deep from TOP) in port and screw areas
// bring local thickness down to 3mm.
// Speaker area: full 5mm (no pocket), grille cuts through.
// Speaker screw heads recessed into top surface.
// ============================================

// --- Import shared parameters from body ---
wall = 3;
$fn  = 32;

rpi_inner_x  = 92;
rpi_inner_y  = 52;
rpi_inner_z  = 61;

spk_inner_y  = 70;
spk_inner_x  = rpi_inner_x;
spk_inner_z  = rpi_inner_z;

outer_x = rpi_inner_y + wall + spk_inner_y + 2 * wall;
outer_y = rpi_inner_x + 2 * wall;
outer_z = rpi_inner_z + 2 * wall;

m3_boss_inner_d = 3.8;

// --- Cap parameters ---
cap_h     = 5;          // total cap thickness
thin_h    = 3;          // thickness in port/screw areas
pocket_d  = cap_h - thin_h;  // pocket depth = 2mm
pocket_z  = cap_h - pocket_d; // pocket starts at this Z (from top)
edge_r    = 1.5;        // rounding radius for top edges

// Screw holes — M3 through-holes (case bosses)
screw_d   = 3.4;
screw_pocket_d = 6.5;    // pocket diameter around each case screw

// Speaker screw head pocket
spk_screw_head_d = 6.5;    // M3 pan head diameter + clearance
spk_screw_head_h = 2;      // recess depth for screw head

// ============================================
// Speaker parameters (measured with Dasqua 2000-2005)
// ============================================
spk_body_x   = 50;     // speaker body width
spk_body_y   = 90;     // speaker body length
spk_mount_x  = 40;     // mounting holes spacing (width)
spk_mount_y  = 75;     // mounting holes spacing (length)
spk_mount_d  = 3.4;    // M3 through-holes for speaker

// Diaphragm (stadium/oblong shape)
spk_dia_w    = 40;     // diaphragm width
spk_dia_l    = 80;     // diaphragm length
spk_dia_r    = spk_dia_w / 2;  // corner radius = 20mm

// Speaker position — centered in speaker compartment
spk_chamber_x = wall + rpi_inner_y + wall;
spk_chamber_y = wall;
spk_center_x  = spk_chamber_x + spk_inner_y / 2;
spk_center_y  = spk_chamber_y + spk_inner_x / 2;

// Speaker grille
grille_slot_w    = 2;
grille_slot_gap  = 2;
grille_margin    = 3;       // inset from diaphragm edge

// ============================================
// USB-C cutout (X1200 UPS, faces up through cap)
// Measured with Dasqua 2000-2005
// ============================================
usbc_overmold_w  = 7.2;
usbc_overmold_l  = 12.2;
usbc_tol         = 1.0;
usbc_cut_w       = usbc_overmold_w + 2 * usbc_tol;  // 9.2mm
usbc_cut_l       = usbc_overmold_l + 2 * usbc_tol;  // 14.2mm
usbc_arc_r       = 8;
usbc_x           = 31.6;
usbc_y           = 61.25;
usbc_pocket_w    = usbc_cut_w + 6;
usbc_pocket_l    = usbc_cut_l + 6;

// ============================================
// Micro-HDMI cutouts (Pi5, 2x ports face up)
// Measured with Dasqua 2000-2005
// ============================================
hdmi_socket_w    = 7.1;
hdmi_socket_h    = 3.64;
hdmi_overmold_x  = 8;
hdmi_overmold_y  = 10;
hdmi_arc_r       = 8;

// HDMI 0 (no overmold)
hdmi0_cut_w      = 6;
hdmi0_cut_l      = 9;
hdmi0_x          = 23.5 + hdmi_socket_h / 2;  // 25.32
hdmi0_y          = 32 + hdmi_socket_w / 2;     // 35.55

// HDMI 1 (overmold passes through)
hdmi1_tol        = 1.0;
hdmi1_cut_w      = hdmi_overmold_x + 2 * hdmi1_tol;  // 10mm
hdmi1_cut_l      = hdmi_overmold_y + 2 * hdmi1_tol;  // 12mm
hdmi1_x          = 23.5 + hdmi_socket_h / 2;  // 25.32
hdmi1_y          = 46 + hdmi_socket_w / 2;     // 49.55

// Combined HDMI pocket
hdmi_pocket_margin = 4;

// ============================================
// Full-size HDMI cutout (WaveShare screen)
// ============================================
fhdmi_socket_w   = 15.12;
fhdmi_socket_h   = 5.6;
fhdmi_tol        = 1.0;
fhdmi_cut_w      = fhdmi_socket_h + 2 * fhdmi_tol;  // 7.6mm
fhdmi_cut_l      = 16;
fhdmi_arc_r      = 10;
fhdmi_x          = 10.88 + fhdmi_socket_h / 2;  // 13.68
fhdmi_y          = 33.35 + fhdmi_socket_w / 2;  // 40.91
fhdmi_pocket_w   = fhdmi_cut_w + 6;
fhdmi_pocket_l   = fhdmi_cut_l + 6;

// ============================================
// 3.5mm Audio jack cutout (round)
// ============================================
audio_d          = 5;    // 3.5mm jack diameter + clearance
audio_tol        = 1.0;
audio_cut_d      = audio_d + 2 * audio_tol;  // 7mm
audio_x          = 10.7 + audio_d / 2;   // 13.2
audio_y          = 56 + audio_d / 2;      // 58.5
audio_pocket_d   = audio_cut_d + 6;       // 13mm

// ============================================
// Case boss positions (must match body)
// ============================================
case_boss_positions = [
    [wall + 58,                                   wall + 2],
    [wall + 58,                                   wall + rpi_inner_x - 2],
    [wall + rpi_inner_y + spk_inner_y + wall - 2, wall + 2],
    [wall + rpi_inner_y + spk_inner_y + wall - 2, wall + rpi_inner_x - 2],
];

// ============================================
// MODULES
// ============================================

// Cap plate with rounded top edges, flat bottom
module cap_plate() {
    intersection() {
        translate([edge_r, edge_r, 0])
            minkowski() {
                cube([
                    outer_x - 2 * edge_r,
                    outer_y - 2 * edge_r,
                    cap_h - edge_r
                ]);
                sphere(r=edge_r, $fn=32);
            }

        translate([-1, -1, 0])
            cube([outer_x + 2, outer_y + 2, cap_h + 1]);
    }
}

// Stadium shape (2D) — rectangle with semicircle ends
module stadium_2d(w, l) {
    r = w / 2;
    straight = l - w;
    hull() {
        translate([0, -straight/2])
            circle(r=r, $fn=64);
        translate([0, straight/2])
            circle(r=r, $fn=64);
    }
}

// Barrel shape (2D) — straight long sides, arc short sides
module barrel_2d(w, l, arc_r) {
    half_w = w / 2;
    half_l = l / 2;
    arc_offset = sqrt(arc_r * arc_r - half_w * half_w);

    intersection() {
        translate([-half_w, -half_l - 1])
            square([w, l + 2]);

        translate([0, half_l - arc_offset])
            circle(r=arc_r, $fn=128);

        translate([0, -(half_l - arc_offset)])
            circle(r=arc_r, $fn=128);
    }
}

// ─── POCKETS (from TOP) ────────────────────────────────────
// NOTE: No speaker body pocket — full 5mm over speaker area

// Speaker screw head pockets (4 corners, from top)
module spk_screw_head_pockets() {
    for (dx = [-1, 1]) {
        for (dy = [-1, 1]) {
            translate([
                spk_center_x + dx * spk_mount_x / 2,
                spk_center_y + dy * spk_mount_y / 2,
                cap_h - spk_screw_head_h
            ])
                cylinder(d=spk_screw_head_d, h=spk_screw_head_h + 1, $fn=32);
        }
    }
}

// Combined pocket for both micro-HDMI ports
module hdmi_pocket() {
    min_x = hdmi0_x - hdmi1_cut_w / 2 - hdmi_pocket_margin;
    max_x = hdmi0_x + hdmi1_cut_w / 2 + hdmi_pocket_margin;
    min_y = hdmi0_y - hdmi0_cut_l / 2 - hdmi_pocket_margin;
    max_y = hdmi1_y + hdmi1_cut_l / 2 + hdmi_pocket_margin;
    translate([min_x, min_y, pocket_z])
        cube([max_x - min_x, max_y - min_y, pocket_d + 1]);
}

// USB-C pocket
module usbc_pocket() {
    translate([
        usbc_x - usbc_pocket_w / 2,
        usbc_y - usbc_pocket_l / 2,
        pocket_z
    ])
        cube([usbc_pocket_w, usbc_pocket_l, pocket_d + 1]);
}

// Full HDMI pocket
module fhdmi_pocket() {
    translate([
        fhdmi_x - fhdmi_pocket_w / 2,
        fhdmi_y - fhdmi_pocket_l / 2,
        pocket_z
    ])
        cube([fhdmi_pocket_w, fhdmi_pocket_l, pocket_d + 1]);
}

// Audio pocket
module audio_pocket() {
    translate([audio_x, audio_y, pocket_z])
        cylinder(d=audio_pocket_d, h=pocket_d + 1, $fn=64);
}

// Case screw pockets — circular around each case boss
module screw_pockets() {
    for (pos = case_boss_positions) {
        translate([pos[0], pos[1], pocket_z])
            cylinder(d=screw_pocket_d, h=pocket_d + 1, $fn=32);
    }
}

// ─── THROUGH-CUTS (full thickness) ─────────────────────────

// Speaker grille — slots clipped to diaphragm stadium shape
module speaker_grille() {
    dia_w = spk_dia_w - 2 * grille_margin;
    dia_l = spk_dia_l - 2 * grille_margin;

    slot_pitch = grille_slot_w + grille_slot_gap;
    n_slots = floor(dia_w / slot_pitch);
    pattern_w = n_slots * slot_pitch - grille_slot_gap;
    offset_x = -pattern_w / 2;

    translate([spk_center_x, spk_center_y, -0.5]) {
        linear_extrude(cap_h + 1) {
            intersection() {
                stadium_2d(dia_w, dia_l);

                for (i = [0 : n_slots - 1]) {
                    translate([offset_x + i * slot_pitch, -dia_l/2])
                        square([grille_slot_w, dia_l]);
                }
            }
        }
    }
}

// Speaker mounting holes (4 corners, through-hole)
module speaker_mount_holes() {
    for (dx = [-1, 1]) {
        for (dy = [-1, 1]) {
            translate([
                spk_center_x + dx * spk_mount_x / 2,
                spk_center_y + dy * spk_mount_y / 2,
                -0.5
            ])
                cylinder(d=spk_mount_d, h=cap_h + 1, $fn=32);
        }
    }
}

// USB-C cutout
module usbc_cutout() {
    translate([usbc_x, usbc_y, -0.5])
        linear_extrude(cap_h + 1)
            barrel_2d(usbc_cut_w, usbc_cut_l, usbc_arc_r);
}

// Micro-HDMI cutouts
module hdmi_cutouts() {
    translate([hdmi0_x, hdmi0_y, -0.5])
        linear_extrude(cap_h + 1)
            barrel_2d(hdmi0_cut_w, hdmi0_cut_l, hdmi_arc_r);

    translate([hdmi1_x, hdmi1_y, -0.5])
        linear_extrude(cap_h + 1)
            barrel_2d(hdmi1_cut_w, hdmi1_cut_l, hdmi_arc_r);
}

// Full-size HDMI cutout
module fhdmi_cutout() {
    translate([fhdmi_x, fhdmi_y, -0.5])
        linear_extrude(cap_h + 1)
            barrel_2d(fhdmi_cut_w, fhdmi_cut_l, fhdmi_arc_r);
}

// 3.5mm audio jack cutout
module audio_cutout() {
    translate([audio_x, audio_y, -0.5])
        cylinder(d=audio_cut_d, h=cap_h + 1, $fn=64);
    translate([audio_x, audio_y, -0.5])
        cylinder(d=13, h=cap_h + 1, $fn=64);
}

// Case screw holes
module case_screw_holes() {
    for (pos = case_boss_positions) {
        translate([pos[0], pos[1], -0.5])
            cylinder(d=screw_d, h=cap_h + 1, $fn=32);
    }
}

// ============================================
// CAP ASSEMBLY
// ============================================

module cap() {
    difference() {
        cap_plate();

        // --- Pockets (from TOP) ---
        spk_screw_head_pockets();   // speaker screw heads (2mm deep)
        hdmi_pocket();
        usbc_pocket();
        fhdmi_pocket();
        audio_pocket();
        screw_pockets();

        // --- Through-cuts (full 5mm) ---
        speaker_grille();
        speaker_mount_holes();
        usbc_cutout();
        hdmi_cutouts();
        fhdmi_cutout();
        audio_cutout();
        case_screw_holes();
        translate([6.9, 51, 3])
            cube([audio_cut_d+5, audio_cut_d + 1, 2]);
        translate([6.9 + audio_cut_d, 50 + audio_cut_d, 3])
            cube([audio_cut_d+5, audio_cut_d + 1, 2]);
        translate([6.7, 27, 3])
            cube([audio_cut_d+5, 32, 2]);        
    }
}

// ============================================
// RENDER
// ============================================

cap();

// ============================================
// DEBUG — uncomment to check positions
// ============================================
// color("blue", 0.3) {
//     translate([usbc_x, usbc_y, cap_h])
//         linear_extrude(1) square([3.2, 9], center=true);
//     translate([hdmi0_x, hdmi0_y, cap_h])
//         linear_extrude(1) square([hdmi_socket_h, hdmi_socket_w], center=true);
//     translate([hdmi1_x, hdmi1_y, cap_h])
//         linear_extrude(1) square([hdmi_socket_h, hdmi_socket_w], center=true);
//     translate([fhdmi_x, fhdmi_y, cap_h])
//         linear_extrude(1) square([fhdmi_socket_h, fhdmi_socket_w], center=true);
//     translate([audio_x, audio_y, cap_h])
//         linear_extrude(1) circle(d=audio_d, $fn=32);
// }
// color("orange", 0.3)
//     translate([spk_center_x, spk_center_y, cap_h])
//         linear_extrude(1) stadium_2d(spk_dia_w, spk_dia_l);

// ============================================
// NOTES
// ============================================
// Cap: 5mm total
//   - Speaker area: FULL 5mm, grille slots cut through
//   - Speaker screw heads: 4x countersink pockets (6.5mm dia, 2mm deep)
//   - Port/case screw areas: 3mm (2mm pockets from top)
//
// Pockets (from TOP surface):
//   - 4x speaker screw heads: 6.5mm dia, 2mm deep
//   - HDMI 0+1: combined rectangle, 2mm deep
//   - USB-C: cutout + 3mm margin, 2mm deep
//   - Full HDMI: cutout + 3mm margin, 2mm deep
//   - Audio: cutout + 3mm margin, 2mm deep
//   - 4x case screws: 10mm dia, 2mm deep
//
// Through-cuts (full 5mm):
//   Speaker grille + 4x M3 speaker mount
//   USB-C: 9.2x14.2mm barrel R=8
//   HDMI 0: 6x9mm barrel R=8
//   HDMI 1: 10x12mm barrel R=8
//   Full HDMI: 7.6x16mm barrel R=10
//   Audio: 7mm circle
//   4x M3 case screws
//
// Print as-is: flat bottom on bed, rounded top up
// ============================================
