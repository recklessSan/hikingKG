import Foundation

struct Track: Codable, Identifiable, Equatable, Hashable {
    var id: UUID = UUID()
    var routeId: UUID?
    var userId: UUID?
    var title: String?
    var description: String?
    var region: String?
    var points: [TrackPoint] = []
    var status: TrackStatus = .draft
    var startedAt: Date?
    var finishedAt: Date?
    var distanceKm: Double = 0
    var durationSeconds: TimeInterval = 0
    var elevationGainM: Double = 0
    var gpxUrl: String?
    var gpxLocalFilename: String?
    var createdAt: Date = Date()

    var pointsCount: Int { points.count }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: Track, rhs: Track) -> Bool {
        lhs.id == rhs.id
    }
}
