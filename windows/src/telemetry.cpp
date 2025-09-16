#include "telemetry.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <numeric>

using namespace std::chrono;

namespace {
std::vector<double> collect_jitter(const std::vector<FrameTelemetry> &frames) {
    std::vector<double> values;
    values.reserve(frames.size());
    for (const auto &frame : frames) {
        values.push_back(frame.jitter_ms);
    }
    std::sort(values.begin(), values.end());
    return values;
}

double percentile(const std::vector<double> &values, double pct) {
    if (values.empty()) {
        return 0.0;
    }
    const auto index = static_cast<size_t>(pct * (values.size() - 1));
    return values[index];
}
}  // namespace

void TelemetryLogger::log_frame(bool visual_on, double effective_hz, double jitter_ms) {
    std::lock_guard guard(mutex_);
    frames_.push_back(FrameTelemetry{steady_clock::now(), visual_on, effective_hz, jitter_ms});
}

SessionSummary TelemetryLogger::build_summary() const {
    std::lock_guard guard(mutex_);
    SessionSummary summary{};
    if (frames_.empty()) {
        return summary;
    }
    auto sum = std::accumulate(
        frames_.begin(), frames_.end(), 0.0, [](double acc, const FrameTelemetry &frame) {
            return acc + frame.effective_hz;
        }
    );
    summary.effective_hz = sum / static_cast<double>(frames_.size());
    auto jitter_values = collect_jitter(frames_);
    summary.jitter_p50 = percentile(jitter_values, 0.50);
    summary.jitter_p95 = percentile(jitter_values, 0.95);
    summary.jitter_p99 = percentile(jitter_values, 0.99);
    return summary;
}

void TelemetryLogger::export_csv(const std::filesystem::path &path) const {
    std::lock_guard guard(mutex_);
    std::ofstream file(path);
    file << "timestamp_us,visual_on,effective_hz,jitter_ms\n";
    for (const auto &frame : frames_) {
        const auto micros = duration_cast<microseconds>(frame.timestamp.time_since_epoch());
        file << micros.count() << ',' << (frame.visual_on ? 1 : 0) << ','
             << frame.effective_hz << ',' << frame.jitter_ms << '\n';
    }
}
