// Features/Recording/RecordingViewModel.swift

import Combine
import CoreLocation
import SwiftUI

@MainActor
class RecordingViewModel: ObservableObject {
    @Published var track: Track
    @Published var isRecording = false
    @Published var currentTime: TimeInterval = 0
    @Published var currentRegion: MKCoordinateRegion = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 42.8746, longitude: 74.5698), // Бишкек
        span: MKCoordinateSpan(latitudeDelta: 0.1, longitudeDelta: 0.1)
    )
    
    private var cancellables = Set<AnyCancellable>()
    private let locationService: LocationService
    
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
        
        // Таймер для currentTime
        Timer.publish(every: 1, on: .main, in: .common)
            .autoconnect()
            .map { [weak self] _ in
                guard let self = self, let start = self.track.startedAt else { return 0.0 }
                return Date().timeIntervalSince(start)
            }
            .assign(to: &$currentTime)
    }
    
    func startRecording() {
        track.status = .recording
        track.startedAt = Date()
        if track.title == nil {
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd HH:mm"
            track.title = "Запись \(formatter.string(from: Date()))"
        }
        isRecording = true
        locationService.startRecording()
    }
    
    func pauseRecording() {
        track.status = .paused
        isRecording = false
        locationService.stopRecording()
    }
    
    func resumeRecording() {
        track.status = .recording
        isRecording = true
        locationService.startRecording()
    }
    
    func stopRecording() {
        track.status = .stopped
        track.finishedAt = Date()
        isRecording = false
        locationService.stopRecording()
        updateStatistics()
        LocalStorageService.shared.saveTrack(track)
    }
    
    private func addPoint(_ point: TrackPoint) {
        guard !track.points.isEmpty || track.startedAt != nil else { return }
        
        if let prev = track.points.last {
            let d = distanceBetween(prev.coordinate, to: point.coordinate)
            track.distanceKm += d / 1000.0
        }
        
        track.points.append(point)
        
        // Обновляем регион карты вокруг последней точки
        let lat = point.latitude
        let lon = point.longitude
        let span = MKCoordinateSpan(latitudeDelta: 0.05, longitudeDelta: 0.05)
        let region = MKCoordinateRegion(center: CLLocationCoordinate2D(latitude: lat, longitude: lon), span: span)
        DispatchQueue.main.async {
            self.currentRegion = region
        }
    }
    
    private func updateStatistics() {
        // Duration
        if let start = track.startedAt,
           let end = track.finishedAt {
            track.durationSeconds = end.timeIntervalSince(start)
        }
        
        // Elevation gain
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
    
    var startTimeText: String {
        let formatter = DurationFormatter()
        formatter.units = [.hours, .minutes, .seconds]
        formatter.allowsPreciseFormatting = false
        return formatter.string(from: currentTime)
    }
    
    var distanceText: String {
        String(format: "%.2f км", track.distanceKm)
    }
    
    var elevationText: String {
        String(format: "+%.0f м", track.elevationGainM)
    }
}

extension DurationFormatter.Units {
    static var hoursMinutesSeconds: DurationFormatter.Units {
        [.hours, .minutes, .seconds]
    }
}

