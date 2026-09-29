<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  searchCenter: { type: Object, required: true },
  hotels: { type: Array, required: true },
  selectedPlaceId: { type: String, default: '' },
})

const emit = defineEmits(['select'])
const mapElement = ref(null)
let map = null
let resultLayer = null

function hotelLabel(hotel) {
  return hotel.name || 'Name not provided'
}

function drawMap() {
  if (!mapElement.value || !props.searchCenter) return

  if (!map) {
    map = L.map(mapElement.value, { scrollWheelZoom: true })
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map)
    resultLayer = L.layerGroup().addTo(map)
  }

  resultLayer.clearLayers()
  const bounds = L.latLngBounds([])
  const center = [props.searchCenter.latitude, props.searchCenter.longitude]
  bounds.extend(center)
  L.circle(center, {
    radius: 5000,
    color: '#1668e3',
    fillColor: '#1668e3',
    fillOpacity: 0.08,
    weight: 2,
  }).addTo(resultLayer)
  L.circleMarker(center, {
    radius: 8,
    color: '#071d49',
    fillColor: '#ffcd00',
    fillOpacity: 1,
    weight: 3,
  }).bindTooltip('ZIP search center').addTo(resultLayer)

  props.hotels.forEach((hotel, index) => {
    const selected = hotel.place_id === props.selectedPlaceId
    const marker = L.circleMarker([hotel.latitude, hotel.longitude], {
      radius: selected ? 12 : 9,
      color: '#ffffff',
      fillColor: selected ? '#ffcd00' : '#1668e3',
      fillOpacity: 1,
      weight: selected ? 4 : 3,
    }).bindTooltip(`${index + 1}. ${hotelLabel(hotel)}`)
    marker.on('click', () => emit('select', hotel.place_id))
    marker.addTo(resultLayer)
    bounds.extend([hotel.latitude, hotel.longitude])
  })

  map.invalidateSize()
  map.fitBounds(bounds.pad(0.14), { maxZoom: 14 })
}

onMounted(drawMap)
watch(
  () => [props.searchCenter, props.hotels, props.selectedPlaceId],
  drawMap,
  { deep: true, flush: 'post' },
)

onBeforeUnmount(() => {
  map?.remove()
  map = null
})
</script>

<template>
  <div class="map-frame">
    <div ref="mapElement" class="hotel-map" aria-label="Map of nearby hotel results"></div>
    <p class="map-note">Markers and results use the same selection. Map © OpenStreetMap contributors.</p>
  </div>
</template>

<style scoped>
.map-frame { overflow: hidden; border: 1px solid #c7d8ef; border-radius: 12px; background: #fff; }
.hotel-map { height: 470px; width: 100%; }
.map-note { margin: 0; padding: 9px 12px; color: #526176; background: #f8faff; font-size: 12px; }
</style>
