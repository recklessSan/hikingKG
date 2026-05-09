import Foundation
import CoreLocation

enum RouteDifficulty: String, Codable, CaseIterable, Identifiable {
    case easy
    case moderate
    case hard
    case expert

    var id: String { rawValue }

    var titleRu: String {
        switch self {
        case .easy: return "Лёгкий"
        case .moderate: return "Средний"
        case .hard: return "Сложный"
        case .expert: return "Экспертный"
        }
    }
}

enum Season: Int, Codable, CaseIterable, Identifiable {
    case january = 1, february, march, april, may, june,
         july, august, september, october, november, december
    var id: Int { rawValue }
}

struct RoutePhoto: Codable, Identifiable, Equatable, Hashable {
    var id: UUID = UUID()
    var assetName: String?
    var remoteUrl: String?
    var caption: String?
}

struct Tag: Codable, Identifiable, Equatable, Hashable {
    var id: UUID = UUID()
    var slug: String
    var title: String
}

struct Poi: Codable, Identifiable, Equatable, Hashable {
    enum Kind: String, Codable {
        case viewpoint, water, camp, hut, pass, summit, danger, parking, other
    }
    var id: UUID = UUID()
    var kind: Kind
    var title: String
    var note: String?
    var latitude: Double
    var longitude: Double

    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
}

struct Route: Codable, Identifiable, Equatable, Hashable {
    var id: UUID = UUID()
    var title: String
    var summary: String
    var description: String
    var regionSlug: String
    var difficulty: RouteDifficulty
    var distanceKm: Double
    var elevationGainM: Double
    var durationHours: Double
    var seasonFrom: Season
    var seasonTo: Season
    var startLatitude: Double
    var startLongitude: Double
    var endLatitude: Double
    var endLongitude: Double
    var gpxUrl: String?
    var gpxLocalFilename: String?
    var photos: [RoutePhoto] = []
    var pois: [Poi] = []
    var tags: [Tag] = []
    var isOfflineAvailable: Bool = true
    var isPublic: Bool = true
    var createdBy: UUID?

    var startCoordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: startLatitude, longitude: startLongitude)
    }

    var endCoordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: endLatitude, longitude: endLongitude)
    }
}
