#include <Windows.h>

namespace
{
    LRESULT CALLBACK WindowProcedure(HWND window, UINT message, WPARAM wParam, LPARAM lParam)
    {
        if (message == WM_DESTROY)
        {
            PostQuitMessage(0);
            return 0;
        }

        return DefWindowProcW(window, message, wParam, lParam);
    }
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int showCommand)
{
    constexpr wchar_t windowClassName[] = L"AutoWindowProjectWindow";

    WNDCLASSW windowClass{};
    windowClass.lpfnWndProc = WindowProcedure;
    windowClass.hInstance = instance;
    windowClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    windowClass.hbrBackground = GetSysColorBrush(COLOR_WINDOW);
    windowClass.lpszClassName = windowClassName;

    if (!RegisterClassW(&windowClass))
    {
        MessageBoxW(nullptr, L"Could not register the window class.", L"AutoWindowProject", MB_OK | MB_ICONERROR);
        return 1;
    }

    const HWND window = CreateWindowExW(
        0, windowClassName, L"AutoWindowProject", WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 800, 450,
        nullptr, nullptr, instance, nullptr);

    if (!window)
    {
        MessageBoxW(nullptr, L"Could not create the window.", L"AutoWindowProject", MB_OK | MB_ICONERROR);
        return 1;
    }

    ShowWindow(window, showCommand);

    MSG message{};
    BOOL result;
    while ((result = GetMessageW(&message, nullptr, 0, 0)) > 0)
    {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }

    if (result == -1)
    {
        MessageBoxW(nullptr, L"Could not retrieve a window message.", L"AutoWindowProject", MB_OK | MB_ICONERROR);
        return 1;
    }

    return static_cast<int>(message.wParam);
}
