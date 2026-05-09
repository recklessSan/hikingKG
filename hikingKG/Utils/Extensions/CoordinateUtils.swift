// Utils/CoordinateUtils.swift

import CoreLocation

extension CLLocationDistance {
    static func distanceBetween(_ from: CLLocationCoordinate2D, to: CLLocationCoordinate2D) -> CLLocationDistance {
        from.distance(from: to)
    }
}

func distanceBetween(_ from: CLLocationCoordinate2D, to: CLLocationCoordinate2D) -> CLLocationDistance {
    from.distance(from: to)
}

