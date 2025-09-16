#pragma once

#include <d3d11.h>
#include <wrl/client.h>

#include <functional>
#include <optional>

#include "telemetry.h"

struct SwapChainConfig {
    double modulation_hz{40.0};
    UINT refresh_rate{120};
};

class SwapChainController {
  public:
    bool initialize(HWND window, const SwapChainConfig &config);
    void render_loop(const std::function<bool()> &frame_callback);
    void shutdown();
    [[nodiscard]] TelemetryLogger &telemetry() { return telemetry_; }

  private:
    Microsoft::WRL::ComPtr<ID3D11Device> device_{};
    Microsoft::WRL::ComPtr<ID3D11DeviceContext> context_{};
    Microsoft::WRL::ComPtr<IDXGISwapChain1> swap_chain_{};
    HANDLE frame_latency_handle_{nullptr};
    SwapChainConfig config_{};
    TelemetryLogger telemetry_{};

    void update_frame_metrics(double delta_ms, bool visual_on);
    bool create_device();
    bool create_swap_chain(HWND window);
};
