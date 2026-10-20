#pragma once

namespace RefView
{
    // Fictional workshop component; not for clinical use.
    class WindowLevelTransform
    {
    public:
        // Throws std::invalid_argument for non-finite inputs, width <= 1,
        // or bounds that overflow or collapse in double precision.
        WindowLevelTransform(double center, double width);

        // Returns [0, 255], rounding halfway values away from zero.
        // Throws std::invalid_argument for a non-finite pixel.
        int Map(double pixel) const;

    private:
        double midpoint_;
        double span_;
        double lower_;
        double upper_;
    };
}
