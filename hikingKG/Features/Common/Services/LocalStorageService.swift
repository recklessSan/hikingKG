// Services/LocalStorageService.swift

import Foundation

final class LocalStorageService {
    static let shared = LocalStorageService()
    
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private let tracksKey = "local_tracks"
    
    private var tracks: [Track] {
        get {
            guard let data = UserDefaults.standard.data(forKey: tracksKey),
                  let tracks = try? decoder.decode([Track].self, from: data) else {
                return []
            }
            return tracks
        }
        set {
            if let data = try? encoder.encode(newValue) {
                UserDefaults.standard.set(data, forKey: tracksKey)
            }
        }
    }
    
    func saveTracks(_ tracks: [Track]) {
        self.tracks = tracks
    }
    
    func loadTracks() -> [Track] {
        return tracks
    }
    
    func saveTrack(_ track: Track) {
        var tracks = loadTracks()
        if let index = tracks.firstIndex(where: { $0.id == track.id }) {
            tracks[index] = track
        } else {
            tracks.append(track)
        }
        saveTracks(tracks)
    }
    
    func deleteTrack(_ track: Track) {
        var tracks = loadTracks()
        tracks.removeAll { $0.id == track.id }
        saveTracks(tracks)
    }
}
