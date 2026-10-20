#include <CppUnitTest.h>

#include "WindowLevelTransform.h"

#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>

using namespace Microsoft::VisualStudio::CppUnitTestFramework;
using RefView::WindowLevelTransform;

namespace AutoWindowProjectTests
{
    TEST_CLASS(LibraryTests)
    {
    public:
        TEST_METHOD(HandoutWorkedExample)
        {
            const WindowLevelTransform transform(50.0, 101.0);
            const double pixels[] = { -100.0, -1.0, 0.0, 50.0, 99.0, 100.0, 500.0 };
            const int expected[] = { 0, 0, 1, 129, 254, 255, 255 };
            for (int i = 0; i < 7; ++i)
            {
                const std::wstring message = L"Pixel " + std::to_wstring(pixels[i]);
                Assert::AreEqual(expected[i], transform.Map(pixels[i]), message.c_str());
            }
        }

        TEST_METHOD(ExactBoundariesAndAdjacentValues)
        {
            const WindowLevelTransform transform(50.0, 101.0);
            const double infinity = std::numeric_limits<double>::infinity();
            Assert::AreEqual(0, transform.Map(std::nextafter(-0.5, -infinity)));
            Assert::AreEqual(0, transform.Map(-0.5));
            Assert::AreEqual(0, transform.Map(std::nextafter(-0.5, infinity)));
            Assert::AreEqual(255, transform.Map(std::nextafter(99.5, -infinity)));
            Assert::AreEqual(255, transform.Map(99.5));
            Assert::AreEqual(255, transform.Map(std::nextafter(99.5, infinity)));
        }

        TEST_METHOD(FractionalPixelsAndNegativeCenter)
        {
            const WindowLevelTransform transform(-10.0, 5.0);
            Assert::AreEqual(0, transform.Map(-12.5));
            Assert::AreEqual(32, transform.Map(-12.0));
            Assert::AreEqual(64, transform.Map(-11.5));
            Assert::AreEqual(128, transform.Map(-10.5));
            Assert::AreEqual(191, transform.Map(-9.5));
            Assert::AreEqual(255, transform.Map(-8.5));
        }

        TEST_METHOD(RoundsNearestAndMidpointUpward)
        {
            const WindowLevelTransform transform(0.5, 3.0);
            Assert::AreEqual(127, transform.Map(-0.001));
            Assert::AreEqual(128, transform.Map(0.0));
            Assert::AreEqual(128, transform.Map(0.001));
        }

        TEST_METHOD(WidthImmediatelyAboveOneIsValid)
        {
            const double width = std::nextafter(1.0, 2.0);
            const double halfSpan = (width - 1.0) / 2.0;
            const WindowLevelTransform transform(0.5, width);
            Assert::AreEqual(0, transform.Map(-halfSpan));
            Assert::AreEqual(128, transform.Map(0.0));
            Assert::AreEqual(255, transform.Map(halfSpan));
        }

        TEST_METHOD(FractionalCenterAndWidth)
        {
            const WindowLevelTransform transform(0.75, 1.5);
            Assert::AreEqual(0, transform.Map(0.0));
            Assert::AreEqual(64, transform.Map(0.125));
            Assert::AreEqual(128, transform.Map(0.25));
            Assert::AreEqual(191, transform.Map(0.375));
            Assert::AreEqual(255, transform.Map(0.5));
        }

        TEST_METHOD(ExtremeFinitePixelsSaturate)
        {
            const WindowLevelTransform transform(50.0, 101.0);
            const double maximum = std::numeric_limits<double>::max();
            Assert::AreEqual(0, transform.Map(-maximum));
            Assert::AreEqual(255, transform.Map(maximum));
        }

        TEST_METHOD(LargestFiniteWidthIsSupported)
        {
            const double maximum = std::numeric_limits<double>::max();
            const WindowLevelTransform transform(0.5, maximum);
            Assert::AreEqual(0, transform.Map(-maximum));
            Assert::AreEqual(64, transform.Map(-maximum / 4.0));
            Assert::AreEqual(128, transform.Map(0.0));
            Assert::AreEqual(191, transform.Map(maximum / 4.0));
            Assert::AreEqual(255, transform.Map(maximum));
        }

        TEST_METHOD(RangeMonotonicityAndDeterminism)
        {
            const double centers[] = { -1000.25, 0.0, 50.0, 1000.5 };
            const double widths[] = { 1.5, 2.0, 101.0, 4096.0 };
            for (double center : centers)
            {
                for (double width : widths)
                {
                    const WindowLevelTransform transform(center, width);
                    const WindowLevelTransform identical(center, width);
                    int previous = 0;
                    for (int i = -8192; i <= 8192; ++i)
                    {
                        const double pixel = i / 2.0;
                        const int output = transform.Map(pixel);
                        Assert::IsTrue(output >= 0 && output <= 255);
                        Assert::IsTrue(output >= previous);
                        Assert::AreEqual(output, transform.Map(pixel));
                        Assert::AreEqual(output, identical.Map(pixel));
                        previous = output;
                    }
                }
            }
        }

        TEST_METHOD(RejectsInvalidWidths)
        {
            const double invalid[] = {
                -100.0, 0.0, 0.5, std::nextafter(1.0, 0.0), 1.0,
                std::numeric_limits<double>::quiet_NaN(),
                std::numeric_limits<double>::infinity(),
                -std::numeric_limits<double>::infinity()
            };
            for (double width : invalid)
            {
                Assert::ExpectException<std::invalid_argument>([width] {
                    const WindowLevelTransform transform(0.0, width);
                });
            }
        }

        TEST_METHOD(RejectsNonFiniteCentersAndPixels)
        {
            const double invalid[] = {
                std::numeric_limits<double>::quiet_NaN(),
                std::numeric_limits<double>::infinity(),
                -std::numeric_limits<double>::infinity()
            };
            const WindowLevelTransform transform(50.0, 101.0);
            for (double value : invalid)
            {
                Assert::ExpectException<std::invalid_argument>([value] {
                    const WindowLevelTransform invalidTransform(value, 101.0);
                });
                Assert::ExpectException<std::invalid_argument>([&transform, value] {
                    transform.Map(value);
                });
            }
        }

        TEST_METHOD(RejectsOverflowingAndCollapsedBounds)
        {
            const double maximum = std::numeric_limits<double>::max();
            for (double center : { -maximum, maximum })
            {
                Assert::ExpectException<std::invalid_argument>([center, maximum] {
                    const WindowLevelTransform transform(center, maximum);
                });
                Assert::ExpectException<std::invalid_argument>([center] {
                    const WindowLevelTransform transform(center, 2.0);
                });
            }
        }
    };
}
