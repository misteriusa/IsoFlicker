#include "swap_chain.h"

#include <dxgi1_3.h>
#include <windows.h>

#include <chrono>

using Microsoft::WRL::ComPtr;

bool SwapChainController::create_device() {
    UINT flags = D3D11_CREATE_DEVICE_BGRA_SUPPORT;
#if defined(_DEBUG)
    flags |= D3D11_CREATE_DEVICE_DEBUG;
#endif
    const D3D_FEATURE_LEVEL levels[] = {
        D3D_FEATURE_LEVEL_11_1,
        D3D_FEATURE_LEVEL_11_0
    };
    D3D_FEATURE_LEVEL selected = D3D_FEATURE_LEVEL_11_0;
    auto hr = D3D11CreateDevice(
        nullptr,
        D3D_DRIVER_TYPE_HARDWARE,
        nullptr,
        flags,
        levels,
        static_cast<UINT>(std::size(levels)),
        D3D11_SDK_VERSION,
        &device_,
        &selected,
        &context_
    );
    return SUCCEEDED(hr);
}

bool SwapChainController::create_swap_chain(HWND window) {
    ComPtr<IDXGIDevice1> dxgi_device;
    auto hr = device_.As(&dxgi_device);
    if (FAILED(hr)) {
        return false;
    }
    ComPtr<IDXGIAdapter> adapter;
    dxgi_device->GetAdapter(&adapter);
    ComPtr<IDXGIFactory2> factory;
    adapter->GetParent(__uuidof(IDXGIFactory2), &factory);

    DXGI_SWAP_CHAIN_DESC1 desc{};
    desc.Format = DXGI_FORMAT_B8G8R8A8_UNORM;
    desc.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    desc.BufferCount = 2;
    desc.Scaling = DXGI_SCALING_STRETCH;
    desc.SwapEffect = DXGI_SWAP_EFFECT_FLIP_DISCARD;
    desc.SampleDesc.Count = 1;
    desc.Width = 0;
    desc.Height = 0;
    desc.Flags = DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT;

    hr = factory->CreateSwapChainForHwnd(
        device_.Get(),
        window,
        &desc,
        nullptr,
        nullptr,
        &swap_chain_
    );
    if (FAILED(hr)) {
        return false;
    }
    swap_chain_->SetMaximumFrameLatency(1);
    frame_latency_handle_ = swap_chain_->GetFrameLatencyWaitableObject();
    return frame_latency_handle_ != nullptr;
}

bool SwapChainController::initialize(HWND window, const SwapChainConfig &config) {
    config_ = config;
    if (!create_device()) {
        return false;
    }
    if (!create_swap_chain(window)) {
        return false;
    }
    return true;
}

void SwapChainController::update_frame_metrics(double delta_ms, bool visual_on) {
    double hz = delta_ms > 0.0 ? 1000.0 / delta_ms : 0.0;
    telemetry_.log_frame(visual_on, hz, delta_ms);
}

void SwapChainController::render_loop(const std::function<bool()> &frame_callback) {
    LARGE_INTEGER frequency{};
    LARGE_INTEGER previous{};
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&previous);
    bool visual_on = false;

    while (frame_callback()) {
        if (frame_latency_handle_) {
            WaitForSingleObjectEx(frame_latency_handle_, INFINITE, FALSE);
        }
        LARGE_INTEGER now{};
        QueryPerformanceCounter(&now);
        double delta_ms = (now.QuadPart - previous.QuadPart) * 1000.0 / frequency.QuadPart;
        previous = now;
        visual_on = !visual_on;
        update_frame_metrics(delta_ms, visual_on);
        swap_chain_->Present(1, 0);
    }
}

void SwapChainController::shutdown() {
    if (frame_latency_handle_) {
        CloseHandle(frame_latency_handle_);
        frame_latency_handle_ = nullptr;
    }
    swap_chain_.Reset();
    context_.Reset();
    device_.Reset();
}
