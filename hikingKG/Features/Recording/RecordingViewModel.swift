import Combine
import CoreLocation
import MapKit
import SwiftUI

@MainActor
final class RecordingViewModel: ObservableObject {
    @Published var track: Track
    @Published var isRecording = false
    @Published var isPaused = false
    @Published var elapsed: TimeInterval = 0
    @Published var currentRegion: MKCoordinateRegion = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 42.8746, longitude: 74.5698), // Bishkek
        span: MKCoordinateSpan(latitudeDelta: 0.1, longitudeDelta: 0.1)
    )

    let locationService: LocationService

    private var cancellables = Set<AnyCancellable>()
    private var resumedAt: Date?
    private var accumulatedSeconds: TimeInterval = 0
    private var timerCancellable: AnyCancellable?

    init(track: Track, locationService: LocationService) {
        self.track = track
        self.locationService = locationService
        setupBindings()
    }

    private func setupBindings() {
        locationService.newPointPublisher
            .receive(on: RunLoop.main)
            .sink { [weak self] point in
                self?.addPoint(point)
            }
            .store(in: &cancellables)
    }

    private func startTimer() {
        timerCancellable?.cancel()
        timerCancellable = Timer.publish(every: 1, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                guard let self else { return }
                self.elapsed = self.computeElapsed()
            }
    }

    private func stopTimer() {
        timerCancellable?.cancel()
        timerCancellable = nil
    }

    private func computeElapsed() -> TimeInterval {
        let live = resumedAt.map { Date().timeIntervalSince($0) } ?? 0
        return accumulatedSeconds + live
    }

    func startRecording() {
        track.status = .recording
        track.startedAt = Date()
        if track.title == nil {
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd HH:mm"
            track.title = "Запись \(formatter.string(from: Date()))"
        }
        accumulatedSeconds = 0
        resumedAt = Date()
        isRecording = true
        isPaused = false
        startTimer()
        locationService.startRecording()
    }

    func pauseRecording() {
        guard isRecording, !isPaused else { return }
        if let resumedAt {
            accumulatedSeconds += Date().timeIntervalSince(resumedAt)
        }
        resumedAt = nil
        track.status = .paused
        isPaused = true
        stopTimer()
        locationService.stopRecording()
    }

    func resumeRecording() {
        guard isRecording, isPaused else { return }
        resumedAt = Date()
        track.status = .recording
        isPaused = false
        startTimer()
        locationService.startRecording()
    }

    func stopRecording() {
        if let resumedAt {
            accumulatedSeconds += Date().timeIntervalSince(resumedAt)
        }
        resumedAt = nil
        track.status = .stopped
        track.finishedAt = Date()
        track.durationSeconds = accumulatedSeconds
        isRecording = false
        isPaused = false
        stopTimer()
        locationService.stopRecording()
        updateStatistics()
        LocalStorageService.shared.saveTrack(track)
    }

    private func addPoint(_ point: TrackPoint) {
        guard isRecording, !isPaused else { return }
        if let prev = track.points.last {
            let d = distanceBetween(prev.coordinate, to: point.coordinate)
            track.distanceKm += d / 1000.0
        }
        track.points.append(point)

        let span = MKCoordinateSpan(latitudeDelta: 0.05, longitudeDelta: 0.05)
        currentRegion = MKCoordinateRegion(
            center: CLLocationCoordinate2D(latitude: point.latitude, longitude: point.longitude),
            span: span
        )
    }

    private func updateStatistics() {
        var elevationGain = 0.0
        for i in 1..<track.points.count {
            let prev = track.points[i - 1]
            let cur = track.points[i]
            if let prevAlt = prev.altitude,
               let curAlt = cur.altitude,
               curAlt > prevAlt {
                elevationGain += curAlt - prevAlt
            }
        }
        track.elevationGainM = elevationGain
    }

    var elapsedText: String {
        let total = Int(elapsed)
        let h = total / 3600
        let m = (total % 3600) / 60
        let s = total % 60
        return String(format: "%02d:%02d:%02d", h, m, s)
    }

    var distanceText: String { String(format: "%.2f км", track.distanceKm) }
    var elevationText: String { String(format: "+%.0f м", track.elevationGainM) }
}
