#include "audio_engine.h"

#include <audioclient.h>
#include <avrt.h>
#include <mmdeviceapi.h>
#include <windows.h>

#include <cmath>
#include <numbers>

using Microsoft::WRL::ComPtr;

bool AudioEngine::create_device() {
    ComPtr<IMMDeviceEnumerator> enumerator;
    auto hr = CoCreateInstance(
        __uuidof(MMDeviceEnumerator),
        nullptr,
        CLSCTX_ALL,
        IID_PPV_ARGS(&enumerator)
    );
    if (FAILED(hr)) {
        return false;
    }
    hr = enumerator->GetDefaultAudioEndpoint(eRender, eConsole, &device_);
    return SUCCEEDED(hr);
}

bool AudioEngine::activate_client() {
    auto hr = device_->Activate(__uuidof(IAudioClient3), CLSCTX_ALL, nullptr, &client_);
    if (FAILED(hr)) {
        return false;
    }
    WAVEFORMATEX format{};
    format.wFormatTag = WAVE_FORMAT_IEEE_FLOAT;
    format.nChannels = 2;
    format.nSamplesPerSec = config_.sample_rate;
    format.wBitsPerSample = 32;
    format.nBlockAlign = (format.nChannels * format.wBitsPerSample) / 8;
    format.nAvgBytesPerSec = format.nBlockAlign * format.nSamplesPerSec;

    REFERENCE_TIME buffer_duration = 3'000'000;  // 300 ms
    hr = client_->Initialize(
        AUDCLNT_SHAREMODE_SHARED,
        AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM,
        buffer_duration,
        0,
        &format,
        nullptr
    );
    if (FAILED(hr)) {
        return false;
    }
    hr = client_->GetService(__uuidof(IAudioRenderClient), &render_client_);
    return SUCCEEDED(hr);
}

bool AudioEngine::initialize(const AudioConfig &config) {
    config_ = config;
    if (!create_device()) {
        return false;
    }
    if (!activate_client()) {
        return false;
    }
    return true;
}

void AudioEngine::render_loop() {
    HANDLE task_handle = AvSetMmThreadCharacteristics(L"Pro Audio", nullptr);
    UINT32 buffer_frames = 0;
    client_->GetBufferSize(&buffer_frames);
    double carrier_phase = 0.0;
    double mod_phase = 0.0;
    const double two_pi = std::numbers::pi * 2.0;
    const double carrier_step = (two_pi * config_.carrier_hz) / config_.sample_rate;
    const double mod_step = (two_pi * config_.modulation_hz) / config_.sample_rate;
    while (running_) {
        UINT32 padding = 0;
        client_->GetCurrentPadding(&padding);
        UINT32 frames = buffer_frames - padding;
        if (frames == 0) {
            Sleep(1);
            continue;
        }
        BYTE *buffer = nullptr;
        render_client_->GetBuffer(frames, &buffer);
        auto *samples = reinterpret_cast<float *>(buffer);
        for (UINT32 i = 0; i < frames; ++i) {
            float carrier = static_cast<float>(std::sin(carrier_phase));
            float envelope = static_cast<float>(0.5 + 0.5 * config_.modulation_depth * std::sin(mod_phase));
            // REVIEW: replace open-loop envelope with raised-cosine pulse generator per PRD.
            // TODO: support nested envelopes (theta->gamma) when scheduler is online.
            float value = carrier * envelope;
            samples[i * 2] = value;
            samples[i * 2 + 1] = value;
            carrier_phase += carrier_step;
            mod_phase += mod_step;
            if (carrier_phase > two_pi) {
                carrier_phase -= two_pi;
            }
            if (mod_phase > two_pi) {
                mod_phase -= two_pi;
            }
        }
        render_client_->ReleaseBuffer(frames, 0);
        Sleep(1);
    }
    if (task_handle) {
        AvRevertMmThreadCharacteristics(task_handle);
    }
}

void AudioEngine::start() {
    if (running_.exchange(true)) {
        return;
    }
    client_->Start();
    render_thread_ = std::thread([this]() { render_loop(); });
}

void AudioEngine::stop() {
    if (!running_.exchange(false)) {
        return;
    }
    client_->Stop();
    if (render_thread_.joinable()) {
        render_thread_.join();
    }
}

void AudioEngine::shutdown() {
    stop();
    render_client_.Reset();
    client_.Reset();
    device_.Reset();
}
