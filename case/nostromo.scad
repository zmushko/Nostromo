// ============================================
// NOSTROMO — RPi5 Terminal + Speaker Case
// ============================================
// External: 134 x 98 x 67mm
// Left:  RPi5 compartment (55mm deep)
// Right: Speaker compartment (70mm deep)
// ============================================

// --- PARAMETERS ---
wall = 3;       // wall thickness
$fn  = 48;

// Internal dimensions
rpi_inner_x  = 92;   // width (along front face)
rpi_inner_y  = 55;   // depth (front to back)
rpi_inner_z  = 61;   // height

spk_inner_y  = 70;   // speaker compartment depth
spk_inner_x  = rpi_inner_x;  // same width
spk_inner_z  = rpi_inner_z;  // same height

// Derived outer dimensions
outer_x = rpi_inner_y + wall + spk_inner_y + 2 * wall;  // 134mm
outer_y = rpi_inner_x + 2 * wall;                        // 98mm
outer_z = rpi_inner_z + 2 * wall;                        // 67mm

// Speaker diaphragm (oval)
spk_dia_x = 82;
spk_dia_z = 43;
spk_corner_r = spk_dia_z / 2;

// ============================================
// MODULES
// ============================================

// M3 heat-set insert boss
// Insert OD: 3.77mm (measured with Dasqua 2000-2005)
// Insert height: 5.22mm (measured)
module m3_boss(h=5.5) {
    difference() {
        cylinder(d=8, h=h, $fn=32);
        cylinder(d=3.6, h=h+1, $fn=32);
    }
}

// Main shell with two internal compartments
module nostromo() {
    difference() {
        // Outer shell
        cube([outer_x, outer_y, outer_z]);

        // RPi compartment (left side, open top)
        translate([wall, wall, wall])
            cube([rpi_inner_y, rpi_inner_x, rpi_inner_z + wall + 1]);

        // Speaker compartment (right side, open top)
        translate([wall + rpi_inner_y + wall, wall, wall])
            cube([spk_inner_y, spk_inner_x, spk_inner_z + wall + 1]);

        // Remove material for top cap
        translate([0, 0, outer_z - wall])
            cube([outer_x, outer_y, 2 * wall + 1]);

        // Screen opening (front face)
        translate([0, wall + 13, wall + 3])
            cube([wall + 1, 77, 52]);

        // Port openings (rear)
        translate([wall + 6, outer_y - wall - 1, wall + 3])
            cube([16, outer_y - wall + 1, 53]);

        // Power button (top face)
        translate([38, 0, 18])
            cube([4, 4, 4]);

        // Cooling vents
        for (i = [0:5]) {
            translate([wall + 8 + i * 4, 0, wall + 10])
                cube([1, 4, 30]);
        }
    }
}

// Ghost: RPi5 stack (for fit check)
module ghost_rpi() {
    color("green", 0.4)
    translate([wall + (rpi_inner_y - 50) / 2,
               wall + (rpi_inner_x - 85.5) / 2,
               wall])
        cube([50, 85.5, 56.5]);
}

// Ghost: speaker (for fit check)
module ghost_speaker() {
    color("orange", 0.4)
    translate([wall + rpi_inner_y + wall + (spk_inner_y - 30) / 2,
               wall + (spk_inner_x - 82) / 2,
               outer_z - 15])
        cube([30, 82, 15]);
}

// ============================================
// RENDER
// ============================================

nostromo();

// Ghost components (comment out before STL export)
// ghost_rpi();
// ghost_speaker();

// M3 mounting bosses
translate([wall + 37, wall + 2, wall + rpi_inner_z - 5.5])
    m3_boss();
translate([wall + 37, wall + rpi_inner_x - 2, wall + rpi_inner_z - 5.5])
    m3_boss();
translate([wall + rpi_inner_y + spk_inner_y + wall - 2, wall + 2, wall + rpi_inner_z - 5.5])
    m3_boss();
translate([wall + rpi_inner_y + spk_inner_y + wall - 2, wall + rpi_inner_x - 2, wall + rpi_inner_z - 5.5])
    m3_boss();

// ============================================
// NOTES:
// ============================================
// All dimensions in mm
// Tolerances: +0.5mm on all component pockets
// M3 insert OD: 3.77mm (Dasqua caliper measurement)
// M3 insert height: 5.22mm (measured)
// Boss hole: 3.6mm for press-fit with soldering iron
// Boss height: 5.5mm (insert + 0.28mm clearance)
// Speaker fires sideways (side-fire for speech clarity)
// ============================================
