import CoreLocation

struct TrackPoint: Codable, Identifiable, Equatable {
    var id: UUID = UUID()
    var latitude: Double
    var longitude: Double
    var altitude: Double?
    var horizontalAccuracy: Double
    var speed: Double
    var heading: Double?
    var timestamp: Date
}

extension TrackPoint {
    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude,
                               longitude: longitude)
    }
}
