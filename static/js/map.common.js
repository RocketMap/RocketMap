/* eslint no-unused-vars: "off" */

var noLabelsStyle = [{
    featureType: 'poi',
    elementType: 'labels',
    stylers: [{
        visibility: 'off'
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.text.stroke',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.text.fill',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}]
var light2Style = [{
    'elementType': 'geometry',
    'stylers': [{
        'hue': '#ff4400'
    }, {
        'saturation': -68
    }, {
        'lightness': -4
    }, {
        'gamma': 0.72
    }]
}, {
    'featureType': 'road',
    'elementType': 'labels.icon'
}, {
    'featureType': 'landscape.man_made',
    'elementType': 'geometry',
    'stylers': [{
        'hue': '#0077ff'
    }, {
        'gamma': 3.1
    }]
}, {
    'featureType': 'water',
    'stylers': [{
        'hue': '#00ccff'
    }, {
        'gamma': 0.44
    }, {
        'saturation': -33
    }]
}, {
    'featureType': 'poi.park',
    'stylers': [{
        'hue': '#44ff00'
    }, {
        'saturation': -23
    }]
}, {
    'featureType': 'water',
    'elementType': 'labels.text.fill',
    'stylers': [{
        'hue': '#007fff'
    }, {
        'gamma': 0.77
    }, {
        'saturation': 65
    }, {
        'lightness': 99
    }]
}, {
    'featureType': 'water',
    'elementType': 'labels.text.stroke',
    'stylers': [{
        'gamma': 0.11
    }, {
        'weight': 5.6
    }, {
        'saturation': 99
    }, {
        'hue': '#0091ff'
    }, {
        'lightness': -86
    }]
}, {
    'featureType': 'transit.line',
    'elementType': 'geometry',
    'stylers': [{
        'lightness': -48
    }, {
        'hue': '#ff5e00'
    }, {
        'gamma': 1.2
    }, {
        'saturation': -23
    }]
}, {
    'featureType': 'transit',
    'elementType': 'labels.text.stroke',
    'stylers': [{
        'saturation': -64
    }, {
        'hue': '#ff9100'
    }, {
        'lightness': 16
    }, {
        'gamma': 0.47
    }, {
        'weight': 2.7
    }]
}]
var darkStyle = [{
    'featureType': 'all',
    'elementType': 'labels.text.fill',
    'stylers': [{
        'saturation': 36
    }, {
        'color': '#b39964'
    }, {
        'lightness': 40
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.text.stroke',
    'stylers': [{
        'visibility': 'on'
    }, {
        'color': '#000000'
    }, {
        'lightness': 16
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'administrative',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 20
    }]
}, {
    'featureType': 'administrative',
    'elementType': 'geometry.stroke',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 17
    }, {
        'weight': 1.2
    }]
}, {
    'featureType': 'landscape',
    'elementType': 'geometry',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 20
    }]
}, {
    'featureType': 'poi',
    'elementType': 'geometry',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 21
    }]
}, {
    'featureType': 'road.highway',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 17
    }]
}, {
    'featureType': 'road.highway',
    'elementType': 'geometry.stroke',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 29
    }, {
        'weight': 0.2
    }]
}, {
    'featureType': 'road.arterial',
    'elementType': 'geometry',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 18
    }]
}, {
    'featureType': 'road.local',
    'elementType': 'geometry',
    'stylers': [{
        'color': '#181818'
    }, {
        'lightness': 16
    }]
}, {
    'featureType': 'transit',
    'elementType': 'geometry',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 19
    }]
}, {
    'featureType': 'water',
    'elementType': 'geometry',
    'stylers': [{
        'lightness': 17
    }, {
        'color': '#525252'
    }]
}]
var pGoStyle = [{
    'featureType': 'landscape.man_made',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#a1f199'
    }]
}, {
    'featureType': 'landscape.natural.landcover',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#37bda2'
    }]
}, {
    'featureType': 'landscape.natural.terrain',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#37bda2'
    }]
}, {
    'featureType': 'poi.attraction',
    'elementType': 'geometry.fill',
    'stylers': [{
        'visibility': 'on'
    }]
}, {
    'featureType': 'poi.business',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#e4dfd9'
    }]
}, {
    'featureType': 'poi.business',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'poi.park',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#37bda2'
    }]
}, {
    'featureType': 'road',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#84b09e'
    }]
}, {
    'featureType': 'road',
    'elementType': 'geometry.stroke',
    'stylers': [{
        'color': '#fafeb8'
    }, {
        'weight': '1.25'
    }]
}, {
    'featureType': 'road.highway',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'water',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#5ddad6'
    }]
}]
var light2StyleNoLabels = [{
    'elementType': 'geometry',
    'stylers': [{
        'hue': '#ff4400'
    }, {
        'saturation': -68
    }, {
        'lightness': -4
    }, {
        'gamma': 0.72
    }]
}, {
    'featureType': 'road',
    'elementType': 'labels.icon'
}, {
    'featureType': 'landscape.man_made',
    'elementType': 'geometry',
    'stylers': [{
        'hue': '#0077ff'
    }, {
        'gamma': 3.1
    }]
}, {
    'featureType': 'water',
    'stylers': [{
        'hue': '#00ccff'
    }, {
        'gamma': 0.44
    }, {
        'saturation': -33
    }]
}, {
    'featureType': 'poi.park',
    'stylers': [{
        'hue': '#44ff00'
    }, {
        'saturation': -23
    }]
}, {
    'featureType': 'water',
    'elementType': 'labels.text.fill',
    'stylers': [{
        'hue': '#007fff'
    }, {
        'gamma': 0.77
    }, {
        'saturation': 65
    }, {
        'lightness': 99
    }]
}, {
    'featureType': 'water',
    'elementType': 'labels.text.stroke',
    'stylers': [{
        'gamma': 0.11
    }, {
        'weight': 5.6
    }, {
        'saturation': 99
    }, {
        'hue': '#0091ff'
    }, {
        'lightness': -86
    }]
}, {
    'featureType': 'transit.line',
    'elementType': 'geometry',
    'stylers': [{
        'lightness': -48
    }, {
        'hue': '#ff5e00'
    }, {
        'gamma': 1.2
    }, {
        'saturation': -23
    }]
}, {
    'featureType': 'transit',
    'elementType': 'labels.text.stroke',
    'stylers': [{
        'saturation': -64
    }, {
        'hue': '#ff9100'
    }, {
        'lightness': 16
    }, {
        'gamma': 0.47
    }, {
        'weight': 2.7
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.text.stroke',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.text.fill',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}]
var darkStyleNoLabels = [{
    'featureType': 'all',
    'elementType': 'labels.text.fill',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.text.stroke',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'administrative',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 20
    }]
}, {
    'featureType': 'administrative',
    'elementType': 'geometry.stroke',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 17
    }, {
        'weight': 1.2
    }]
}, {
    'featureType': 'landscape',
    'elementType': 'geometry',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 20
    }]
}, {
    'featureType': 'poi',
    'elementType': 'geometry',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 21
    }]
}, {
    'featureType': 'road.highway',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 17
    }]
}, {
    'featureType': 'road.highway',
    'elementType': 'geometry.stroke',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 29
    }, {
        'weight': 0.2
    }]
}, {
    'featureType': 'road.arterial',
    'elementType': 'geometry',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 18
    }]
}, {
    'featureType': 'road.local',
    'elementType': 'geometry',
    'stylers': [{
        'color': '#181818'
    }, {
        'lightness': 16
    }]
}, {
    'featureType': 'transit',
    'elementType': 'geometry',
    'stylers': [{
        'color': '#000000'
    }, {
        'lightness': 19
    }]
}, {
    'featureType': 'water',
    'elementType': 'geometry',
    'stylers': [{
        'lightness': 17
    }, {
        'color': '#525252'
    }]
}]
var pGoStyleNoLabels = [{
    'featureType': 'landscape.man_made',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#a1f199'
    }]
}, {
    'featureType': 'landscape.natural.landcover',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#37bda2'
    }]
}, {
    'featureType': 'landscape.natural.terrain',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#37bda2'
    }]
}, {
    'featureType': 'poi.attraction',
    'elementType': 'geometry.fill',
    'stylers': [{
        'visibility': 'on'
    }]
}, {
    'featureType': 'poi.business',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#e4dfd9'
    }]
}, {
    'featureType': 'poi.business',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'poi.park',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#37bda2'
    }]
}, {
    'featureType': 'road',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#84b09e'
    }]
}, {
    'featureType': 'road',
    'elementType': 'geometry.stroke',
    'stylers': [{
        'color': '#fafeb8'
    }, {
        'weight': '1.25'
    }]
}, {
    'featureType': 'road.highway',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'water',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#5ddad6'
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.text.stroke',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.text.fill',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'all',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}]
var pGoStyleDay = [{
    'featureType': 'landscape.man_made',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#99f291'
    }]
}, {
    'featureType': 'landscape.natural.landcover',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#00af8f'
    }]
}, {
    'featureType': 'landscape.natural.terrain',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#00af8f'
    }]
}, {
    'featureType': 'landscape.natural',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#00af8f'
    }]
}, {
    'featureType': 'poi.attraction',
    'elementType': 'geometry.fill',
    'stylers': [{
        'visibility': 'on'
    }]
}, {
    'featureType': 'poi.business',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#e4dfd9'
    }]
}, {
    'featureType': 'poi.business',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'poi.park',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#00af8f'
    }]
}, {
    'featureType': 'road',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#7eb2a4'
    }]
}, {
    'featureType': 'road',
    'elementType': 'geometry.stroke',
    'stylers': [{
        'color': '#ffff92'
    }, {
        'weight': '2'
    }]
}, {
    'featureType': 'road.highway',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'water',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#1688da'
    }]
}, {
    'featureType': 'poi.attraction',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#e4fdee'
    }]
}, {
    'featureType': 'poi.sports_complex',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#d4ffbc'
    }]
}]
var pGoStyleNight = [{
    'featureType': 'landscape.man_made',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#12a085'
    }]
}, {
    'featureType': 'landscape.natural.landcover',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#02706a'
    }]
}, {
    'featureType': 'landscape.natural.terrain',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#02706a'
    }]
}, {
    'featureType': 'landscape.natural',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#02706a'
    }]
}, {
    'featureType': 'poi',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#6da298'
    }]
}, {
    'featureType': 'poi.medical',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#6da298'
    }]
}, {
    'featureType': 'poi.attraction',
    'elementType': 'geometry.fill',
    'stylers': [{
        'visibility': 'on'
    }]
}, {
    'featureType': 'poi.business',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#1fba9c'
    }]
}, {
    'featureType': 'poi.business',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'poi.park',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#02706a'
    }]
}, {
    'featureType': 'transit',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#428290'
    }]
}, {
    'featureType': 'road',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#316589'
    }]
}, {
    'featureType': 'road',
    'elementType': 'geometry.stroke',
    'stylers': [{
        'color': '#7f8b60'
    }, {
        'weight': '2'
    }]
}, {
    'featureType': 'road.highway',
    'elementType': 'labels.icon',
    'stylers': [{
        'visibility': 'off'
    }]
}, {
    'featureType': 'water',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#1e4fbc'
    }]
}, {
    'featureType': 'poi.attraction',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#1fba9c'
    }]
}, {
    'featureType': 'poi.sports_complex',
    'elementType': 'geometry.fill',
    'stylers': [{
        'color': '#1fba9c'
    }]
}]

var pokemonSprites = {
    columns: 28,
    iconWidth: 80,
    iconHeight: 80,
    spriteWidth: 2240,
    spriteHeight: 1440,
    filename: 'static/icons-large-sprite.png',
    name: 'High-Res'
}

//
// LocalStorage helpers
//

var StoreTypes = {
    Boolean: {
        parse: function (str) {
            switch (str.toLowerCase()) {
                case '1':
                case 'true':
                case 'yes':
                    return true
                default:
                    return false
            }
        },
        stringify: function (b) {
            return b ? 'true' : 'false'
        }
    },
    JSON: {
        parse: function (str) {
            return JSON.parse(str)
        },
        stringify: function (json) {
            return JSON.stringify(json)
        }
    },
    String: {
        parse: function (str) {
            return str
        },
        stringify: function (str) {
            return str
        }
    },
    Number: {
        parse: function (str) {
            return parseInt(str, 10)
        },
        stringify: function (number) {
            return number.toString()
        }
    }
}

// set the default parameters for you map here
var StoreOptions = {
    'map_style': {
        default: 'roadmap', // roadmap, satellite, hybrid, nolabels_style, dark_style, style_light2, style_pgo, dark_style_nl, style_pgo_day, style_pgo_night, style_pgo_dynamic
        type: StoreTypes.String
    },
    'remember_select_exclude': {
        default: [],
        type: StoreTypes.JSON
    },
    'remember_select_notify': {
        default: [],
        type: StoreTypes.JSON
    },
    'remember_select_rarity_notify': {
        default: [], // Common, Uncommon, Rare, Very Rare, Ultra Rare
        type: StoreTypes.JSON
    },
    'remember_text_perfection_notify': {
        default: '',
        type: StoreTypes.Number
    },
    'remember_text_level_notify': {
        default: 0,
        type: StoreTypes.Number
    },
    'excludedRarity': {
        default: 0, // 0: none, 1: <=Common, 2: <=Uncommon, 3: <=Rare, 4: <=Very Rare, 5: <=Ultra Rare
        type: StoreTypes.Number
    },
    'showRaids': {
        default: false,
        type: StoreTypes.Boolean
    },
    'showActiveRaidsOnly': {
        default: false,
        type: StoreTypes.Boolean
    },
    'showRaidMinLevel': {
        default: 1,
        type: StoreTypes.Number
    },
    'showRaidMaxLevel': {
        default: 5,
        type: StoreTypes.Number
    },
    'showGyms': {
        default: false,
        type: StoreTypes.Boolean
    },
    'useGymSidebar': {
        default: false,
        type: StoreTypes.Boolean
    },
    'showOpenGymsOnly': {
        default: false,
        type: StoreTypes.Boolean
    },
    'showTeamGymsOnly': {
        default: 0,
        type: StoreTypes.Number
    },
    'showLastUpdatedGymsOnly': {
        default: 0,
        type: StoreTypes.Number
    },
    'minGymLevel': {
        default: 0,
        type: StoreTypes.Number
    },
    'maxGymLevel': {
        default: 6,
        type: StoreTypes.Number
    },
    'showPokemon': {
        default: true,
        type: StoreTypes.Boolean
    },
    'showPokemonStats': {
        default: true,
        type: StoreTypes.Boolean
    },
    'showPokestops': {
        default: true,
        type: StoreTypes.Boolean
    },
    'showLuredPokestopsOnly': {
        default: 0,
        type: StoreTypes.Number
    },
    'showScanned': {
        default: false,
        type: StoreTypes.Boolean
    },
    'showSpawnpoints': {
        default: false,
        type: StoreTypes.Boolean
    },
    'showRanges': {
        default: false,
        type: StoreTypes.Boolean
    },
    'playSound': {
        default: false,
        type: StoreTypes.Boolean
    },
    'playCries': {
        default: false,
        type: StoreTypes.Boolean
    },
    'geoLocate': {
        default: false,
        type: StoreTypes.Boolean
    },
    'lockMarker': {
        default: isTouchDevice(), // default to true if touch device
        type: StoreTypes.Boolean
    },
    'startAtUserLocation': {
        default: false,
        type: StoreTypes.Boolean
    },
    'followMyLocation': {
        default: false,
        type: StoreTypes.Boolean
    },
    'followMyLocationPosition': {
        default: [],
        type: StoreTypes.JSON
    },
    'scanHere': {
        default: false,
        type: StoreTypes.Boolean
    },
    'scanHereAlerted': {
        default: false,
        type: StoreTypes.Boolean
    },
    'pokemonIcons': {
        default: 'highres',
        type: StoreTypes.String
    },
    'iconSizeModifier': {
        default: 0,
        type: StoreTypes.Number
    },
    'scaleByRarity': {
        default: true,
        type: StoreTypes.Boolean
    },
    'upscalePokemon': {
        default: false,
        type: StoreTypes.Boolean
    },
    'upscaledPokemon': {
        default: [],
        type: StoreTypes.JSON
    },
    'searchMarkerStyle': {
        default: 'pokesition',
        type: StoreTypes.String
    },
    'locationMarkerStyle': {
        default: 'mobile',
        type: StoreTypes.String
    },
    'zoomLevel': {
        default: 16,
        type: StoreTypes.Number
    },
    'maxClusterZoomLevel': {
        default: 14,
        type: StoreTypes.Number
    },
    'clusterZoomOnClick': {
        default: false,
        type: StoreTypes.Boolean
    },
    'clusterGridSize': {
        default: 60,
        type: StoreTypes.Number
    },
    'processPokemonChunkSize': {
        default: 100,
        type: StoreTypes.Number
    },
    'processPokemonIntervalMs': {
        default: 100,
        type: StoreTypes.Number
    },
    'mapServiceProvider': {
        default: 'googlemaps',
        type: StoreTypes.String
    },
    'isBounceDisabled': {
        default: false,
        type: StoreTypes.Boolean
    },
    'showLocationMarker': {
        default: true,
        type: StoreTypes.Boolean
    },
    'isLocationMarkerMovable': {
        default: false,
        type: StoreTypes.Boolean
    },
    'showSearchMarker': {
        default: true,
        type: StoreTypes.Boolean
    },
    'isSearchMarkerMovable': {
        default: false,
        type: StoreTypes.Boolean
    }
}

var Store = {
    getOption: function (key) {
        var option = StoreOptions[key]
        if (!option) {
            throw new Error('Store key was not defined ' + key)
        }
        return option
    },
    get: function (key) {
        var option = this.getOption(key)
        var optionType = option.type
        var rawValue = localStorage[key]
        if (rawValue === null || rawValue === undefined) {
            return option.default
        }
        var value = optionType.parse(rawValue)
        return value
    },
    set: function (key, value) {
        var option = this.getOption(key)
        var optionType = option.type || StoreTypes.String
        var rawValue = optionType.stringify(value)
        localStorage[key] = rawValue
    },
    reset: function (key) {
        localStorage.removeItem(key)
    }
}

var mapData = {
    pokemons: {},
    gyms: {},
    pokestops: {},
    lurePokemons: {},
    scanned: {},
    spawnpoints: {}
}

// Populated by a JSON request.
var pokemonRarities = {}

function updatePokemonRarities() {
    $.getJSON('static/dist/data/rarity.json').done(function (data) {
        pokemonRarities = data
    }).fail(function () {
        // Could be disabled/removed.
        console.log("Couldn't load dynamic rarity JSON.")
    })
}

function getPokemonRarity(pokemonId) {
    if (pokemonRarities.hasOwnProperty(pokemonId)) {
        return pokemonRarities[pokemonId]
    }

    return ''
}

function getGoogleSprite(index, sprite, displayHeight) {
    displayHeight = Math.max(displayHeight, 3)
    var scale = displayHeight / sprite.iconHeight
    // Crop icon just a tiny bit to avoid bleedover from neighbor
    var scaledIconSize = new google.maps.Size(scale * sprite.iconWidth - 1, scale * sprite.iconHeight - 1)
    var scaledIconOffset = new google.maps.Point(
        (index % sprite.columns) * sprite.iconWidth * scale + 0.5,
        Math.floor(index / sprite.columns) * sprite.iconHeight * scale + 0.5)
    var scaledSpriteSize = new google.maps.Size(scale * sprite.spriteWidth, scale * sprite.spriteHeight)
    var scaledIconCenterOffset = new google.maps.Point(scale * sprite.iconWidth / 2, scale * sprite.iconHeight / 2)

    return {
        url: sprite.filename,
        size: scaledIconSize,
        scaledSize: scaledSpriteSize,
        origin: scaledIconOffset,
        anchor: scaledIconCenterOffset
    }
}

function setupPokemonMarkerDetails(item, map, scaleByRarity = true, isNotifyPkmn = false) {
    const pokemonIndex = item['pokemon_id'] - 1
    const sprite = pokemonSprites

    var markerDetails = {
        sprite: sprite
    }
    var iconSize = (map.getZoom() - 3) * (map.getZoom() - 3) * 0.2 + Store.get('iconSizeModifier')
    rarityValue = 2

    if (Store.get('upscalePokemon')) {
        const upscaledPokemon = Store.get('upscaledPokemon')
        var rarityValue = isNotifyPkmn || (upscaledPokemon.indexOf(item['pokemon_id']) !== -1) ? 29 : 2
    }

    if (scaleByRarity) {
        const rarityValues = {
            'very rare': 30,
            'ultra rare': 40,
            'legendary': 50
        }

        const pokemonRarity = getPokemonRarity(item['pokemon_id']).toLowerCase()

        if (rarityValues.hasOwnProperty(pokemonRarity)) {
            rarityValue = rarityValues[pokemonRarity]
        }
    }

    iconSize += rarityValue
    markerDetails.rarityValue = rarityValue
    markerDetails.icon = getGoogleSprite(pokemonIndex, sprite, iconSize)
    markerDetails.iconSize = iconSize

    return markerDetails
}

function setupPokemonMarker(item, map, isBounceDisabled, scaleByRarity = true, isNotifyPkmn = false) {
    // Scale icon size up with the map exponentially, also size with rarity.
    const markerDetails = setupPokemonMarkerDetails(item, map, scaleByRarity, isNotifyPkmn)
    const icon = markerDetails.icon

    var marker = new google.maps.Marker({
        position: {
            lat: item['latitude'],
            lng: item['longitude']
        },
        zIndex: 9949 + markerDetails.rarityValue,
        icon: icon,
        animationDisabled: isBounceDisabled
    })

    return marker
}

function updatePokemonMarker(item, map, scaleByRarity = true, isNotifyPkmn = false) {
    // Scale icon size up with the map exponentially, also size with rarity.
    const markerDetails = setupPokemonMarkerDetails(item, map, scaleByRarity, isNotifyPkmn)
    const icon = markerDetails.icon
    const marker = item.marker

    marker.setIcon(icon)
}

function updatePokemonLabel(item) {
    // Only update label when Pokémon has been encountered.
    if (item['cp'] !== null && item['cpMultiplier'] !== null) {
        item.marker.infoWindow.setContent(pokemonLabel(item))
    }
}

function updatePokemonLabels(pokemonList) {
    $.each(pokemonList, function (key, value) {
        var item = pokemonList[key]

        updatePokemonLabel(item)
    })
}

function isTouchDevice() {
    // Should cover most browsers
    return 'ontouchstart' in window || navigator.maxTouchPoints
}

function isMobileDevice() {
    //  Basic mobile OS (not browser) detection
    return (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent))
}
