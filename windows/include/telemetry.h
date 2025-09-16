#pragma once

#include <chrono>
#include <filesystem>
#include <mutex>
#include <vector>

struct FrameTelemetry {
    std::chrono::steady_clock::time_point timestamp{};
    bool visual_on{false};
    double effective_hz{0.0};
    double jitter_ms{0.0};
};

struct SessionSummary {
    double effective_hz{0.0};
    double jitter_p50{0.0};
    double jitter_p95{0.0};
    double jitter_p99{0.0};
    unsigned long dropped_frames{0};
};

class TelemetryLogger {
  public:
    void log_frame(bool visual_on, double effective_hz, double jitter_ms);
    [[nodiscard]] SessionSummary build_summary() const;
    void export_csv(const std::filesystem::path &path) const;

  private:
    mutable std::mutex mutex_{};
    std::vector<FrameTelemetry> frames_{};
};
