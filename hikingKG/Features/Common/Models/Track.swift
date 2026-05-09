import Foundation

struct Track: Codable, Identifiable, Equatable {
    var id: UUID = UUID()
    var title: String?
    var description: String?
    var region: String? // например, "Ala Archa"
    var points: [TrackPoint] = []
    var status: TrackStatus = .draft
    var startedAt: Date?
    var finishedAt: Date?
    var distanceKm: Double = 0
    var durationSeconds: TimeInterval = 0
    var elevationGainM: Double = 0
    var createdAt: Date = Date()
}

