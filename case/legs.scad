// Leg profile - Nostromo stand
module leg_profile() {
    polygon(points=[
        [0, 0],        // O - right angle
        [0, 31.94],    // A - top
        [9.23, 28.10], // B - 10mm along hypotenuse from A
        [20, 0]        // D - 20mm along base from O
    ]);
}

wall = 3;

module leg() {
    difference() {
        linear_extrude(height=15)
            leg_profile();

        translate([wall, wall, wall])
            cube([50, 50, 15 - 2*wall]);

        // M3 hole in the base (ZX plane)
        translate([10, -1, 15/2])
            rotate([-90, 0, 0])
                cylinder(h=wall+2, d=3.2, $fn=32);
    }
}

// First leg
leg();

// Second leg, offset 58mm along Z
translate([0, 0, 58])
    leg();

// Connecting bar along the base (XZ plane), trimmed to leg profile
intersection() {
    translate([0, 0, 15])
        cube([20, wall, 58 - 15]);
    linear_extrude(height=58 + 15)
        leg_profile();
}






