import SwiftUI

struct TrackListView: View {
    @StateObject private var viewModel = TrackListViewModel()

    var body: some View {
        Group {
            if viewModel.tracks.isEmpty {
                EmptyStateView(systemImage: "figure.hiking",
                               title: "Записей пока нет",
                               message: "Начните запись на вкладке «Запись», чтобы сохранить первый трек.")
            } else {
                List {
                    ForEach(viewModel.tracks) { track in
                        NavigationLink(value: track) {
                            TrackRow(track: track)
                        }
                    }
                    .onDelete { indexSet in
                        for index in indexSet {
                            viewModel.delete(viewModel.tracks[index])
                        }
                    }
                }
            }
        }
        .navigationTitle("Мои треки")
        .navigationDestination(for: Track.self) { track in
            TrackDetailView(track: track)
        }
        .onAppear { viewModel.reload() }
    }
}

private struct TrackRow: View {
    let track: Track

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(track.title ?? "Без названия")
                .font(.headline)
            HStack(spacing: 12) {
                Label(String(format: "%.2f км", track.distanceKm), systemImage: "ruler")
                Label(durationText, systemImage: "clock")
                if track.elevationGainM > 0 {
                    Label(String(format: "+%.0f м", track.elevationGainM), systemImage: "arrow.up.right")
                }
            }
            .font(.subheadline)
            .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }

    private var durationText: String {
        let total = Int(track.durationSeconds)
        let h = total / 3600
        let m = (total % 3600) / 60
        return String(format: "%dч %02dм", h, m)
    }
}
