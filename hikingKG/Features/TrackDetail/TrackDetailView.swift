import SwiftUI
import CoreLocation

struct TrackDetailView: View {
    @StateObject private var viewModel: TrackDetailViewModel

    init(track: Track) {
        _viewModel = StateObject(wrappedValue: TrackDetailViewModel(track: track))
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                RouteMapView(coordinates: coordinates,
                             startCoordinate: coordinates.first,
                             endCoordinate: coordinates.last)
                    .frame(height: 280)
                    .clipShape(RoundedRectangle(cornerRadius: 12))

                statsGrid

                if let description = viewModel.track.description, !description.isEmpty {
                    Text(description)
                        .font(.body)
                }

                Divider()

                Button {
                    if let url = viewModel.exportGPX() {
                        share(url: url)
                    }
                } label: {
                    Label("Экспорт в GPX", systemImage: "square.and.arrow.up")
                }
                .buttonStyle(.borderedProminent)
            }
            .padding()
        }
        .navigationTitle(viewModel.track.title ?? "Трек")
    }

    private var coordinates: [CLLocationCoordinate2D] {
        viewModel.track.points.map { $0.coordinate }
    }

    private var statsGrid: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            statCard(title: "Дистанция", value: String(format: "%.2f км", viewModel.track.distanceKm))
            statCard(title: "Время", value: durationText)
            statCard(title: "Набор высоты", value: String(format: "+%.0f м", viewModel.track.elevationGainM))
            statCard(title: "Точек", value: "\(viewModel.track.pointsCount)")
        }
    }

    private func statCard(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title).font(.caption).foregroundStyle(.secondary)
            Text(value).font(.title3.weight(.semibold))
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }

    private var durationText: String {
        let total = Int(viewModel.track.durationSeconds)
        let h = total / 3600
        let m = (total % 3600) / 60
        let s = total % 60
        return String(format: "%dч %02dм %02dс", h, m, s)
    }

    private func share(url: URL) {
        #if canImport(UIKit)
        let activity = UIActivityViewController(activityItems: [url], applicationActivities: nil)
        UIApplication.shared.connectedScenes
            .compactMap { ($0 as? UIWindowScene)?.keyWindow?.rootViewController }
            .first?
            .present(activity, animated: true)
        #endif
    }
}
