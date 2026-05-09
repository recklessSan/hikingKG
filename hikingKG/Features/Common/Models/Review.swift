import Foundation

struct Review: Codable, Identifiable, Equatable, Hashable {
    var id: UUID = UUID()
    var routeId: UUID
    var userId: UUID
    var rating: Int // 1...5
    var text: String?
    var createdAt: Date = Date()
}
