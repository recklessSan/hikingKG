import Combine
import Foundation

@MainActor
final class TrackListViewModel: ObservableObject {
    @Published var tracks: [Track] = []

    func reload() {
        tracks = LocalStorageService.shared.loadTracks()
            .sorted(by: { ($0.finishedAt ?? $0.createdAt) > ($1.finishedAt ?? $1.createdAt) })
    }

    func delete(_ track: Track) {
        LocalStorageService.shared.deleteTrack(track)
        reload()
    }
}
