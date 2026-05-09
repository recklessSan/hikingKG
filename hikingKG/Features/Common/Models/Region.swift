import Foundation
import CoreLocation

struct Region: Codable, Identifiable, Equatable, Hashable {
    var id: UUID = UUID()
    var slug: String
    var name: String
    var nameRu: String?
    var nameKy: String?
    var summary: String
    var centerLatitude: Double
    var centerLongitude: Double
    var coverAssetName: String?

    var center: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: centerLatitude, longitude: centerLongitude)
    }
}
