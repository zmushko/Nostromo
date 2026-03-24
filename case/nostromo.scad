// ============================================
// NOSTROMO — RPi5 Terminal + Speaker Case
// ============================================
// External: 126 x 94 x 65mm
// Left:  RPi5 compartment (53mm deep)
// Right: Speaker compartment (70mm deep)
// ============================================

// --- PARAMETERS --- undefined
wall = 3;       // wall thickness
$fn  = 32;       // number of facets for cylinders/spheres (higher = smoother, but slower render)

// Internal dimensions
rpi_inner_x  = 92;   // width (along front face)
rpi_inner_y  = 52;   // depth (front to back)
rpi_inner_z  = 61;   // height

spk_inner_y  = 70;   // speaker compartment depth
spk_inner_x  = rpi_inner_x;  // same width
spk_inner_z  = rpi_inner_z;  // same height

// Derived outer dimensions
outer_x = rpi_inner_y + wall + spk_inner_y + 2 * wall;  // 55+3+70+2*3 = 134mm
outer_y = rpi_inner_x + 2 * wall;                        // 92+6 = 98mm
outer_z = rpi_inner_z + 2 * wall;                        // 61+6 = 67mm

// Speaker diaphragm (oval)
spk_dia_x = 82;
spk_dia_z = 43;
spk_corner_r = spk_dia_z / 2;

// RPi5 mounting hole pattern in the center divider
rpi_mount_hole_d = 3.0;
rpi_mount_spacing_y = 58;
rpi_mount_spacing_z = 49;
rpi_board_size_y = 85.5;
rpi_board_size_z = 56.5;
rpi_mount_edge_offset_y = 3.5;
rpi_mount_edge_offset_z = 3.5;
rpi_ports_wall_clearance = 0;
rpi_floor_clearance = 0;
rpi_board_y = wall + rpi_inner_x - rpi_board_size_y - rpi_ports_wall_clearance;
rpi_board_z = wall + rpi_floor_clearance;

// inner diameter of bosses for M3 screws (for 2mm clearance on 2.5mm screws)
m3_boss_inner_d = 3.8;

// External screwdriver access arches for the lower RPi5 mounting holes
screwdriver_access_d = 6;
screwdriver_access_depth = wall + 2;

// Port cutout in the back wall of the RPi compartment
port_cutout_x = wall + 7;
port_cutout_z = wall + 1;
port_cutout_w = 17;
port_cutout_h = 54;
port_cutout_depth = outer_y - wall + 1;

// ============================================
// MODULES
// ============================================

module m3_boss(h=6) {
    difference() {
        cylinder(d=8, h=h, $fn=32);
        cylinder(d=m3_boss_inner_d, h=h+1, $fn=32);
    }
}

module rpi5_partition_mount_holes() {
    for (y_offset = [0, rpi_mount_spacing_y]) {
        for (z_offset = [0, rpi_mount_spacing_z]) {
                translate([
                    wall + rpi_inner_y - 1,
                    rpi_board_y + rpi_mount_edge_offset_y + y_offset,
                    rpi_board_z + rpi_mount_edge_offset_z + z_offset
                ])
                rotate([0, 90, 0])
                    cylinder(d=rpi_mount_hole_d, h=wall + 2, $fn=32);
        }
    }
}

module lower_rpi_screwdriver_access_arches() {
    for (y_pos = [
        rpi_board_y + rpi_mount_edge_offset_y,
        rpi_board_y + rpi_mount_edge_offset_y + rpi_mount_spacing_y
    ]) {
        translate([outer_x - wall - 1, y_pos - screwdriver_access_d / 2, 0])
            cube([screwdriver_access_depth, screwdriver_access_d, rpi_board_z + rpi_mount_edge_offset_z]);

        translate([outer_x - wall - 1, y_pos, rpi_board_z + rpi_mount_edge_offset_z])
            rotate([0, 90, 0])
                cylinder(d=screwdriver_access_d, h=screwdriver_access_depth, $fn=32);
    }
}

module screwdriver_access_arches() {
    for (y_pos = [
        rpi_board_y + rpi_mount_edge_offset_y - wall *2, 
        rpi_board_y + rpi_mount_edge_offset_y - wall + screwdriver_access_d,
        rpi_board_y + rpi_mount_edge_offset_y + rpi_mount_spacing_y - wall * 2,
        rpi_board_y + rpi_mount_edge_offset_y + rpi_mount_spacing_y - wall + screwdriver_access_d 
    ]) {
        translate([outer_x - wall - spk_inner_y, y_pos, wall])
            cube([spk_inner_y, wall, wall + 1]);

        // translate([outer_x - wall - 1, y_pos, rpi_board_z + rpi_mount_edge_offset_z])
        //     rotate([0, 90, 0])
        //         cylinder(d=screwdriver_access_d, h=screwdriver_access_depth, $fn=32);
    }
}

module make_arc(y) {
    difference() {
        translate([
            outer_x - wall - spk_inner_y, 
            y, 
            rpi_board_z + rpi_mount_edge_offset_z
        ])
            rotate([0, 90, 0])
                cylinder(d=12, h=spk_inner_y, $fn=32);
        
        translate([
            outer_x - wall - spk_inner_y, 
            y, 
            rpi_board_z + rpi_mount_edge_offset_z
        ])
            rotate([0, 90, 0])
                cylinder(d=screwdriver_access_d, h=spk_inner_y + wall + 1, $fn=32);
    
        translate([
            outer_x - wall - spk_inner_y, 
            y - screwdriver_access_d / 2, 
            0
        ])
            cube([spk_inner_y + wall + 1, screwdriver_access_d, rpi_board_z + rpi_mount_edge_offset_z]);
    }
}

// Main shell with two internal compartments
module nostromo() {
    difference() {
        // Outer shell (positioned so min coords = 0)
        // translate([0, 0, 0])
        //     cube([outer_x, outer_y, outer_z]);
        translate([wall, wall, wall])
            minkowski() {
                cube([outer_x - 2 * wall, outer_y - 2 * wall, outer_z - wall]);
                sphere(wall, $fn=32);
            }

        // RPi compartment (left side, open top)
        translate([wall, wall, wall])
            cube([rpi_inner_y, rpi_inner_x, rpi_inner_z + wall + 1]);

        // Speaker compartment (right side, open top)
        translate([wall + rpi_inner_y + wall, wall, wall])
            cube([spk_inner_y, spk_inner_x, spk_inner_z + wall + 1]);

        // mounting holes for RPi5 in the divider wall
        rpi5_partition_mount_holes();

        // external screwdriver access for the two lower RPi5 mounting holes
        lower_rpi_screwdriver_access_arches();

        // remove material for top cap
        translate([0, 0, outer_z - wall - 1])
            cube([outer_x, outer_y, 2 * wall + 1]);

        // remove material for screen (front face)
        translate([0, wall + 13, wall + 3])
            cube([wall + 1, 75, 51]);

        // remove material for ports
        translate([port_cutout_x, outer_y - wall - 1, port_cutout_z])
            cube([port_cutout_w, port_cutout_depth, port_cutout_h]);

            // color("red", 0.4)
        //remove material for corner
        // translate([0, 80, wall + 1])
        //     cube([16, 20, 54]);

        // cut top for test fitting (comment out before STL export)
        // translate([0, 0, wall + 6])
        //     cube([outer_x + 1, outer_y + 1, wall + 100]);

        // remove material for power button (round hole)
        translate([38.5, 0, wall + 14])
            rotate([-90, 0, 0])
                cylinder(d=7, h=8, $fn=32);

        // cat material for cooling vents (top face, left side)
        for (i = [0:4]) {
            translate([wall + 12 + i * 4, 0, wall + 8])
                cube([2, 4, 42]);
        }

        // cut material for scruwdriver access to lower RPi5 mounting holes (back face)
        translate([outer_x - wall - spk_inner_y, rpi_board_y + rpi_mount_edge_offset_y - wall, 0])
            cube([spk_inner_y + wall + 1, screwdriver_access_d, wall + 1]);

        translate([outer_x - wall - spk_inner_y, rpi_board_y + rpi_mount_edge_offset_y - wall + rpi_mount_spacing_y, 0])
            cube([spk_inner_y + wall + 1, screwdriver_access_d, wall + 1]);

        // cat small hole for the wired speaker
        translate([wall + 20, outer_y - 20, rpi_inner_z + wall - 2])
                cube([100, 2, 1]);

        translate([wall + 58, wall + 20, 0])
            cylinder(d=m3_boss_inner_d, h=wall + 1, $fn=32);
        translate([wall + 58, wall + rpi_inner_x - 14, 0])
            cylinder(d=m3_boss_inner_d, h=wall + 1, $fn=32);
        // cut for test fitting (comment out before STL export)
        // translate([62, 0, 0])
        //     cube([outer_x + 1, outer_y + 1, wall + 100]);
    }
}

// Ghost: RPi5 stack (for fit check)
// module ghost_rpi() {
//     color("green", 0.4)
//         translate([wall + (rpi_inner_y - 50) / 2,
//              rpi_board_y,
//              rpi_board_z])
//          cube([50, rpi_board_size_y, rpi_board_size_z]);
// }

// // Ghost: speaker (for fit check)
// module ghost_speaker() {
//     color("orange", 0.4)
//     translate([wall + rpi_inner_y + wall + (spk_inner_y - 30) / 2,
//                wall + (spk_inner_x - 82) / 2,
//                outer_z - 15])
//         cube([30, 82, 15]);
// }



// ============================================
// RENDER
// ============================================

nostromo();

// Ghost components (comment out before STL export)
// ghost_rpi();
// ghost_speaker();

        // M3 mounting bosses (4 per compartment)
// translate([wall + rpi_inner_y + wall + 2, wall + 2, wall + rpi_inner_z - 6])
//     m3_boss();
// translate([wall + rpi_inner_y + wall + 2, wall + rpi_inner_x -2,  wall + rpi_inner_z - 6])
//     m3_boss();

// translate([wall + 32, wall + 2, wall + rpi_inner_z - 6])
//     m3_boss();
// translate([wall + 32, wall + rpi_inner_x -2,  wall + rpi_inner_z - 6])
//     m3_boss();
// translate([wall + rpi_inner_y + spk_inner_y + wall - 2, wall + 2, wall + rpi_inner_z - 6])
//     m3_boss();
// translate([wall + rpi_inner_y + spk_inner_y + wall - 2, wall + rpi_inner_x - 2, wall + rpi_inner_z - 6])
//     m3_boss();

// M3 mounting bosses (4 per compartment, full height for through-hole screws)
translate([wall + 58, wall + 2, wall + rpi_inner_z - 7])
    m3_boss();
translate([wall + 58, wall + rpi_inner_x -2,  wall + rpi_inner_z - 7])
    m3_boss();
translate([wall + rpi_inner_y + spk_inner_y + wall - 2, wall + 2, wall + rpi_inner_z - 7])
    m3_boss();
translate([wall + rpi_inner_y + spk_inner_y + wall - 2, wall + rpi_inner_x - 2, wall + rpi_inner_z - 7])
    m3_boss();

translate([wall + 58, wall + 20, 0])
    m3_boss();
translate([wall + 58, wall + rpi_inner_x - 14, 0])
    m3_boss();


screwdriver_access_arches();
make_arc(rpi_board_y + rpi_mount_edge_offset_y);
make_arc(rpi_board_y + rpi_mount_edge_offset_y + rpi_mount_spacing_y);

// ============================================
// NOTES:
// ============================================
// Outer dimensions: 134 x 98 x 67mm
// Left compartment (RPi): 55 x 92 x 61mm internal
// Right compartment (spk): 70 x 92 x 61mm internal
// Speaker fires upward through top face
// Screen opening on front face (100 x 94mm side)
// ============================================
