// Utils/CoordinateUtils.swift

import CoreLocation

extension CLLocationCoordinate2D {
    func distance(to other: CLLocationCoordinate2D) -> CLLocationDistance {
        let a = CLLocation(latitude: latitude, longitude: longitude)
        let b = CLLocation(latitude: other.latitude, longitude: other.longitude)
        return a.distance(from: b)
    }
}

extension CLLocationDistance {
    static func distanceBetween(_ from: CLLocationCoordinate2D, to: CLLocationCoordinate2D) -> CLLocationDistance {
        from.distance(to: to)
    }
}

func distanceBetween(_ from: CLLocationCoordinate2D, to: CLLocationCoordinate2D) -> CLLocationDistance {
    from.distance(to: to)
}
