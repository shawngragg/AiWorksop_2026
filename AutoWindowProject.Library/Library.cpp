#include "WindowLevelTransform.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace RefView
{
    WindowLevelTransform::WindowLevelTransform(double center, double width)
    {
        if (!std::isfinite(center) || !std::isfinite(width) || width <= 1.0)
        {
            throw std::invalid_argument("Center and width must be finite; width must be greater than 1.");
        }

        midpoint_ = center - 0.5;
        span_ = width - 1.0;
        lower_ = midpoint_ - span_ / 2.0;
        upper_ = midpoint_ + span_ / 2.0;

        if (!std::isfinite(lower_) || !std::isfinite(upper_) || lower_ >= upper_)
        {
            throw std::invalid_argument("Window bounds must be finite and distinct in double precision.");
        }
    }

    int WindowLevelTransform::Map(double pixel) const
    {
        if (!std::isfinite(pixel))
        {
            throw std::invalid_argument("Pixel value must be finite.");
        }

        if (pixel <= lower_)
        {
            return 0;
        }
        if (pixel > upper_)
        {
            return 255;
        }

        // Algebraically equal to ((pixel - midpoint) / span + 0.5) * 255, but measuring from
        // the lower bound and multiplying before dividing keeps exact .5 results exact, so
        // std::round breaks ties away from zero as specified. Divide first only when the
        // product could overflow.
        const double offset = pixel - lower_;
        const double display = span_ <= std::numeric_limits<double>::max() / 255.0
            ? offset * 255.0 / span_
            : offset / span_ * 255.0;
        return static_cast<int>(std::clamp(std::round(display), 0.0, 255.0));
    }
}
