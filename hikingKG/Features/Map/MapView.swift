import SwiftUI
import MapKit
import CoreLocation

struct RouteMapView: View {
    let coordinates: [CLLocationCoordinate2D]
    let startCoordinate: CLLocationCoordinate2D?
    let endCoordinate: CLLocationCoordinate2D?

    @State private var region: MKCoordinateRegion = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 41.5, longitude: 75.0),
        span: MKCoordinateSpan(latitudeDelta: 6.0, longitudeDelta: 6.0)
    )

    var body: some View {
        Map(coordinateRegion: $region,
            annotationItems: annotations) { annotation in
            MapMarker(coordinate: annotation.coordinate, tint: annotation.tint)
        }
        .onAppear { fitRegion() }
        .accessibilityLabel("Карта маршрута")
    }

    private struct Annotation: Identifiable {
        let id = UUID()
        let coordinate: CLLocationCoordinate2D
        let tint: Color
    }

    private var annotations: [Annotation] {
        var items: [Annotation] = []
        if let start = startCoordinate {
            items.append(Annotation(coordinate: start, tint: .green))
        }
        if let end = endCoordinate {
            items.append(Annotation(coordinate: end, tint: .red))
        }
        return items
    }

    private func fitRegion() {
        let pts = coordinates.isEmpty
            ? [startCoordinate, endCoordinate].compactMap { $0 }
            : coordinates
        guard !pts.isEmpty else { return }
        let lats = pts.map { $0.latitude }
        let lons = pts.map { $0.longitude }
        let minLat = lats.min() ?? 0
        let maxLat = lats.max() ?? 0
        let minLon = lons.min() ?? 0
        let maxLon = lons.max() ?? 0
        let center = CLLocationCoordinate2D(
            latitude: (minLat + maxLat) / 2,
            longitude: (minLon + maxLon) / 2
        )
        let span = MKCoordinateSpan(
            latitudeDelta: max(0.05, (maxLat - minLat) * 1.4),
            longitudeDelta: max(0.05, (maxLon - minLon) * 1.4)
        )
        region = MKCoordinateRegion(center: center, span: span)
    }
}
