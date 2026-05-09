import Foundation

struct User: Codable, Identifiable, Equatable, Hashable {
    var id: UUID = UUID()
    var displayName: String
    var email: String?
    var avatarAssetName: String?
    var bio: String?
    var preferredLocale: String = "ru"
    var createdAt: Date = Date()
}
