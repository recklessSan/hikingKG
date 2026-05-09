import Combine
import Foundation

@MainActor
final class TrackDetailViewModel: ObservableObject {
    @Published var track: Track

    init(track: Track) {
        self.track = track
    }

    func exportGPX() -> URL? {
        let exporter = GPXExporter()
        let xml = exporter.makeGPX(for: track)
        let filename = "track-\(track.id.uuidString).gpx"
        let url = FileManager.default.temporaryDirectory.appendingPathComponent(filename)
        do {
            try xml.data(using: .utf8)?.write(to: url, options: .atomic)
            return url
        } catch {
            return nil
        }
    }
}
