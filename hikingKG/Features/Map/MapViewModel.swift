import Foundation
import MapKit
import CoreLocation

@MainActor
final class MapViewModel: ObservableObject {
    @Published var region: MKCoordinateRegion

    init(center: CLLocationCoordinate2D = CLLocationCoordinate2D(latitude: 41.5, longitude: 75.0),
         spanDegrees: Double = 4.0) {
        self.region = MKCoordinateRegion(
            center: center,
            span: MKCoordinateSpan(latitudeDelta: spanDegrees, longitudeDelta: spanDegrees)
        )
    }
}
