import Foundation
import CoreLocation

enum GPXImportError: Error {
    case invalidXML
    case noTrackOrRoute
}

final class GPXImporter: NSObject {
    struct Result {
        var trackPoints: [TrackPoint]
        var waypoints: [Poi]
        var name: String?
    }

    func importTrack(from data: Data) throws -> Result {
        let parser = XMLParser(data: data)
        let delegate = GPXParserDelegate()
        parser.delegate = delegate
        guard parser.parse() else {
            throw GPXImportError.invalidXML
        }
        if delegate.trackPoints.isEmpty && delegate.waypoints.isEmpty {
            throw GPXImportError.noTrackOrRoute
        }
        return Result(trackPoints: delegate.trackPoints,
                      waypoints: delegate.waypoints,
                      name: delegate.name)
    }

    func importTrack(from url: URL) throws -> Result {
        let data = try Data(contentsOf: url)
        return try importTrack(from: data)
    }
}

private final class GPXParserDelegate: NSObject, XMLParserDelegate {
    var trackPoints: [TrackPoint] = []
    var waypoints: [Poi] = []
    var name: String?

    private var currentElement: String = ""
    private var currentLat: Double?
    private var currentLon: Double?
    private var currentEle: Double?
    private var currentTime: Date?
    private var currentName: String?
    private var insideTrkpt = false
    private var insideWpt = false
    private var insideRtept = false

    private static let isoFormatter: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()
    private static let isoFormatterNoFraction: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()

    func parser(_ parser: XMLParser,
                didStartElement elementName: String,
                namespaceURI: String?,
                qualifiedName qName: String?,
                attributes attributeDict: [String : String] = [:]) {
        currentElement = elementName
        switch elementName {
        case "trkpt":
            insideTrkpt = true
            currentLat = attributeDict["lat"].flatMap(Double.init)
            currentLon = attributeDict["lon"].flatMap(Double.init)
            currentEle = nil
            currentTime = nil
        case "wpt":
            insideWpt = true
            currentLat = attributeDict["lat"].flatMap(Double.init)
            currentLon = attributeDict["lon"].flatMap(Double.init)
            currentName = nil
        case "rtept":
            insideRtept = true
            currentLat = attributeDict["lat"].flatMap(Double.init)
            currentLon = attributeDict["lon"].flatMap(Double.init)
            currentName = nil
        default:
            break
        }
    }

    func parser(_ parser: XMLParser, foundCharacters string: String) {
        let trimmed = string.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        switch currentElement {
        case "ele":
            currentEle = Double(trimmed)
        case "time":
            currentTime = GPXParserDelegate.isoFormatter.date(from: trimmed)
                ?? GPXParserDelegate.isoFormatterNoFraction.date(from: trimmed)
        case "name":
            if insideWpt || insideRtept {
                currentName = (currentName ?? "") + trimmed
            } else if !insideTrkpt {
                name = (name ?? "") + trimmed
            }
        default:
            break
        }
    }

    func parser(_ parser: XMLParser,
                didEndElement elementName: String,
                namespaceURI: String?,
                qualifiedName qName: String?) {
        switch elementName {
        case "trkpt":
            if let lat = currentLat, let lon = currentLon {
                let point = TrackPoint(
                    latitude: lat,
                    longitude: lon,
                    altitude: currentEle,
                    horizontalAccuracy: -1,
                    speed: -1,
                    heading: nil,
                    timestamp: currentTime ?? Date()
                )
                trackPoints.append(point)
            }
            insideTrkpt = false
        case "wpt", "rtept":
            if let lat = currentLat, let lon = currentLon {
                let poi = Poi(kind: .other,
                              title: currentName ?? "Точка",
                              note: nil,
                              latitude: lat,
                              longitude: lon)
                waypoints.append(poi)
            }
            insideWpt = false
            insideRtept = false
        default:
            break
        }
        currentElement = ""
    }
}
