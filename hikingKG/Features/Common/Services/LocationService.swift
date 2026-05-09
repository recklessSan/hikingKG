// Services/LocationService.swift

import CoreLocation
import Combine

@MainActor
final class LocationService: NSObject, ObservableObject {
    private let manager = CLLocationManager()
    
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined
    @Published var currentLocation: CLLocation?
    @Published var isRecording = false
    
    // Для новых точек
    var newPointPublisher = PassthroughSubject<TrackPoint, Never>()
    
    private var lastPoint: CLLocation?
    
    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.distanceFilter = 5.0
    }
    
    func requestWhenInUse() {
        manager.requestWhenInUseAuthorization()
    }
    
    func requestAlways() {
        manager.requestAlwaysAuthorization()
    }
    
    func startRecording() {
        guard authorizationStatus == .authorizedWhenInUse ||
              authorizationStatus == .authorizedAlways else { return }
        
        manager.startUpdatingLocation()
        isRecording = true
    }
    
    func stopRecording() {
        manager.stopUpdatingLocation()
        isRecording = false
    }
    
    func setDistanceFilter(_ value: Double) {
        manager.distanceFilter = value
    }
}

// MARK: - CLLocationManagerDelegate

extension LocationService: CLLocationManagerDelegate {
    nonisolated func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            self.currentLocation = location
            
            let point = self.makeTrackPoint(from: location)
            self.newPointPublisher.send(point)
        }
    }
    
    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        DispatchQueue.main.async { [weak self] in
            self?.authorizationStatus = manager.authorizationStatus
        }
    }
    
    nonisolated func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        // Можно добавить логирование
    }
}

// MARK: - Helpers

extension LocationService {
    private func makeTrackPoint(from location: CLLocation) -> TrackPoint {
        TrackPoint(
            latitude: location.coordinate.latitude,
            longitude: location.coordinate.longitude,
            altitude: location.altitude,
            horizontalAccuracy: location.horizontalAccuracy,
            speed: location.speed,
            heading: location.course,
            timestamp: location.timestamp
        )
    }
}

