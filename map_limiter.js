mapID = document.querySelector("div[id^='map_']").id;


var southWest = L.latLng(-90, -180),
northEast = L.latLng(90, 180);
var bounds = L.latLngBounds(southWest, northEast);

window[mapID].setZoom(3)
window[mapID].options.minZoom = 3
window[mapID].on('drag', function() {
    window[mapID].panInsideBounds(bounds, { animate: false });
});

