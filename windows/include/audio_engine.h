#pragma once

#include <mmdeviceapi.h>
#include <wrl/client.h>

#include <atomic>
#include <thread>

struct AudioConfig {
    double carrier_hz{1000.0};
    double modulation_hz{40.0};
    double modulation_depth{1.0};
    UINT32 sample_rate{48000};
};

class AudioEngine {
  public:
    bool initialize(const AudioConfig &config);
    void start();
    void stop();
    void shutdown();

  private:
    Microsoft::WRL::ComPtr<IMMDevice> device_{};
    Microsoft::WRL::ComPtr<IAudioClient3> client_{};
    Microsoft::WRL::ComPtr<IAudioRenderClient> render_client_{};
    AudioConfig config_{};
    std::atomic<bool> running_{false};
    std::thread render_thread_{};

    bool create_device();
    bool activate_client();
    void render_loop();
};
