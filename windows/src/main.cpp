#include <windows.h>
#include <wrl/client.h>

#include <string>

#include "audio_engine.h"
#include "swap_chain.h"
#include "telemetry.h"

namespace {
const wchar_t kWindowClassName[] = L"IsoFlickerWindow";

LRESULT CALLBACK WindowProc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam) {
    switch (msg) {
        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
        default:
            return DefWindowProc(hwnd, msg, wparam, lparam);
    }
}

HWND create_window(HINSTANCE instance) {
    WNDCLASSEXW wc{};
    wc.cbSize = sizeof(wc);
    wc.hInstance = instance;
    wc.lpszClassName = kWindowClassName;
    wc.lpfnWndProc = WindowProc;
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
    RegisterClassExW(&wc);
    return CreateWindowExW(
        0,
        kWindowClassName,
        L"IsoFlicker (Preview)",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        1280,
        720,
        nullptr,
        nullptr,
        instance,
        nullptr
    );
}

bool process_messages() {
    MSG msg{};
    while (PeekMessage(&msg, nullptr, 0, 0, PM_REMOVE)) {
        if (msg.message == WM_QUIT) {
            return false;
        }
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return true;
}

bool init_audio_engine(AudioEngine &audio, HWND hwnd) {
    AudioConfig config{};
    if (!audio.initialize(config)) {
        MessageBoxW(hwnd, L"Audio engine initialization failed", L"IsoFlicker", MB_ICONERROR);
        return false;
    }
    audio.start();
    return true;
}

bool init_swap_chain(SwapChainController &swap_chain, HWND hwnd) {
    SwapChainConfig config{};
    if (!swap_chain.initialize(hwnd, config)) {
        MessageBoxW(hwnd, L"Swap chain initialization failed", L"IsoFlicker", MB_ICONERROR);
        return false;
    }
    return true;
}

void shutdown_services(AudioEngine &audio, SwapChainController &swap_chain) {
    swap_chain.shutdown();
    audio.shutdown();
}

bool bootstrap_system(HWND hwnd, AudioEngine &audio, SwapChainController &swap_chain) {
    if (!init_audio_engine(audio, hwnd)) {
        return false;
    }
    if (!init_swap_chain(swap_chain, hwnd)) {
        audio.shutdown();
        return false;
    }
    return true;
}

}  // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int show_command) {
    if (FAILED(CoInitializeEx(nullptr, COINIT_MULTITHREADED))) {
        MessageBoxW(nullptr, L"Failed to initialize COM", L"IsoFlicker", MB_ICONERROR);
        return -1;
    }
    HWND hwnd = create_window(instance);
    if (!hwnd) {
        CoUninitialize();
        return -1;
    }
    ShowWindow(hwnd, show_command);
    SetThreadExecutionState(ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED | ES_CONTINUOUS);

    AudioEngine audio;
    SwapChainController swap_chain;
    if (!bootstrap_system(hwnd, audio, swap_chain)) {
        DestroyWindow(hwnd);
        SetThreadExecutionState(ES_CONTINUOUS);
        CoUninitialize();
        return -1;
    }

    auto frame_callback = [&]() {
        return process_messages();
    };
    // REVIEW: hook visual frame generation into real render graph with brightness control.
    swap_chain.render_loop(frame_callback);

    SessionSummary summary = swap_chain.telemetry().build_summary();
    swap_chain.telemetry().export_csv(L"telemetry.csv");
    (void)summary;
    shutdown_services(audio, swap_chain);
    SetThreadExecutionState(ES_CONTINUOUS);
    CoUninitialize();
    return 0;
}
