import Foundation

struct Report: Codable, Identifiable, Equatable, Hashable {
    enum Reason: String, Codable, CaseIterable, Identifiable {
        case incorrectInfo
        case unsafeRoute
        case spam
        case other
        var id: String { rawValue }
    }

    enum Target: String, Codable {
        case route
        case track
        case review
        case user
    }

    var id: UUID = UUID()
    var target: Target
    var targetId: UUID
    var reportedBy: UUID
    var reason: Reason
    var comment: String?
    var createdAt: Date = Date()
}
