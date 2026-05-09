import Foundation

final class GPXExporter {
    private static let isoFormatter: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()

    func makeGPX(for track: Track) -> String {
        var xml = #"<?xml version="1.0" encoding="UTF-8"?>"# + "\n"
        xml += #"<gpx version="1.1" creator="hikingKG" xmlns="http://www.topografix.com/GPX/1/1">"# + "\n"
        if let title = track.title {
            xml += "  <metadata><name>\(escape(title))</name></metadata>\n"
        }
        xml += "  <trk>\n"
        xml += "    <name>\(escape(track.title ?? "Track"))</name>\n"
        xml += "    <trkseg>\n"
        for point in track.points {
            xml += "      <trkpt lat=\"\(point.latitude)\" lon=\"\(point.longitude)\">\n"
            if let alt = point.altitude {
                xml += "        <ele>\(alt)</ele>\n"
            }
            xml += "        <time>\(GPXExporter.isoFormatter.string(from: point.timestamp))</time>\n"
            xml += "      </trkpt>\n"
        }
        xml += "    </trkseg>\n"
        xml += "  </trk>\n"
        xml += "</gpx>\n"
        return xml
    }

    func makeGPX(forRouteWaypoints route: Route) -> String {
        var xml = #"<?xml version="1.0" encoding="UTF-8"?>"# + "\n"
        xml += #"<gpx version="1.1" creator="hikingKG" xmlns="http://www.topografix.com/GPX/1/1">"# + "\n"
        xml += "  <metadata><name>\(escape(route.title))</name></metadata>\n"

        // Start/end as wpt
        xml += waypointXML(lat: route.startLatitude,
                           lon: route.startLongitude,
                           name: "\(route.title) — старт")
        xml += waypointXML(lat: route.endLatitude,
                           lon: route.endLongitude,
                           name: "\(route.title) — финиш")
        for poi in route.pois {
            xml += waypointXML(lat: poi.latitude,
                               lon: poi.longitude,
                               name: poi.title)
        }
        xml += "</gpx>\n"
        return xml
    }

    @discardableResult
    func writeGPX(for track: Track, to url: URL) throws -> URL {
        let xml = makeGPX(for: track)
        try xml.data(using: .utf8)?.write(to: url, options: .atomic)
        return url
    }

    private func waypointXML(lat: Double, lon: Double, name: String) -> String {
        "  <wpt lat=\"\(lat)\" lon=\"\(lon)\"><name>\(escape(name))</name></wpt>\n"
    }

    private func escape(_ s: String) -> String {
        s.replacingOccurrences(of: "&", with: "&amp;")
         .replacingOccurrences(of: "<", with: "&lt;")
         .replacingOccurrences(of: ">", with: "&gt;")
         .replacingOccurrences(of: "\"", with: "&quot;")
         .replacingOccurrences(of: "'", with: "&apos;")
    }
}
