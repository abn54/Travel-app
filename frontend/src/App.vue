<script setup>
import { onMounted, ref } from 'vue'
import HotelMap from './HotelMap.vue'

const API = 'http://127.0.0.1:8000/api'
const hotelName = ref('')
const results = ref([])
const users = ref([])
const bookings = ref([])
const selectedStay = ref(null)
const selectedUserId = ref('')
const historyUserId = ref('')
const searched = ref(false)
const loading = ref(false)
const loadingHistory = ref(false)
const zipCode = ref('16802')
const zipLoading = ref(false)
const zipLocation = ref(null)
const zipError = ref('')
const nearbyZipCode = ref('')
const nearbyLoading = ref(false)
const nearbyHotels = ref([])
const nearbyCenter = ref(null)
const nearbyError = ref('')
const nearbyNoResults = ref(false)
const nearbySearched = ref(false)
const selectedNearbyPlaceId = ref('')
const localHotels = ref([])
const localQuery = ref('')
const localLoading = ref(false)
const localSavingPlaceId = ref('')
const localError = ref('')
const localMessage = ref('')
const chatQuestion = ref('Which saved hotel has the lowest simulated nightly rate on 2026-10-10?')
const chatLoading = ref(false)
const chatError = ref('')
const chatResult = ref(null)
const error = ref('')
const message = ref('')

function formatDate(value) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${value}T12:00:00`))
}

function formatMoney(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function formatDistance(value) {
  return typeof value === 'number' ? `${Math.round(value).toLocaleString()} m from the ZIP center` : 'Distance not provided'
}

function centerLabel(center) {
  if (!center) return ''
  return [center.postcode, center.locality].filter(Boolean).join(' · ')
}

function demoNightLabel(night) {
  const roomLabel = night.available_rooms === 1 ? 'room' : 'rooms'
  return `${formatDate(night.stay_date)} · ${formatMoney(night.nightly_rate_usd)} · ${night.available_rooms} simulated ${roomLabel}`
}

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, options)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || 'The booking service is unavailable. Please try again.')
  return body
}

async function loadUsers() {
  users.value = await request('/users')
  if (!selectedUserId.value && users.value.length) selectedUserId.value = users.value[0].user_id
}

async function loadBookings() {
  loadingHistory.value = true
  error.value = ''
  try {
    const suffix = historyUserId.value ? `?user_id=${encodeURIComponent(historyUserId.value)}` : ''
    bookings.value = await request(`/bookings${suffix}`)
  } catch (err) {
    error.value = err.message
  } finally {
    loadingHistory.value = false
  }
}

async function search() {
  searched.value = true
  error.value = ''
  message.value = ''
  loading.value = true
  try {
    results.value = await request(`/search?hotel_name=${encodeURIComponent(hotelName.value)}`)
  } catch (err) {
    error.value = err.message
    results.value = []
  } finally {
    loading.value = false
  }
}

async function requestZipLocation(path) {
  if (zipLoading.value) return
  zipLocation.value = null
  zipError.value = ''
  zipLoading.value = true
  try {
    zipLocation.value = await request(path)
  } catch (err) {
    zipError.value = err.message
  } finally {
    zipLoading.value = false
  }
}

function lookupZip() {
  return requestZipLocation(`/zip-location?postcode=${encodeURIComponent(zipCode.value.trim())}`)
}

async function searchNearbyHotels() {
  const postcode = nearbyZipCode.value.trim()
  nearbySearched.value = true
  nearbyError.value = ''
  nearbyNoResults.value = false
  nearbyHotels.value = []
  nearbyCenter.value = null
  selectedNearbyPlaceId.value = ''

  if (!/^\d{5}$/.test(postcode)) {
    nearbyError.value = 'Enter a five-digit U.S. ZIP code.'
    return
  }

  nearbyLoading.value = true
  try {
    const result = await request(`/hotel-discovery?postcode=${encodeURIComponent(postcode)}`)
    nearbyCenter.value = result.search_center
    nearbyHotels.value = result.hotels
    nearbyNoResults.value = result.status === 'no_results'
    selectedNearbyPlaceId.value = result.hotels[0]?.place_id || ''
  } catch (err) {
    nearbyError.value = err.message
  } finally {
    nearbyLoading.value = false
  }
}

function selectNearbyHotel(placeId) {
  selectedNearbyPlaceId.value = placeId
}

async function loadLocalHotels() {
  localLoading.value = true
  localError.value = ''
  try {
    const suffix = localQuery.value.trim() ? `?query=${encodeURIComponent(localQuery.value.trim())}` : ''
    localHotels.value = await request(`/local-hotels${suffix}`)
  } catch (err) {
    localError.value = err.message
  } finally {
    localLoading.value = false
  }
}

async function saveLocalHotel(hotel) {
  if (localSavingPlaceId.value || !nearbyCenter.value) return
  localError.value = ''
  localMessage.value = ''
  localSavingPlaceId.value = hotel.place_id
  try {
    const saved = await request('/local-hotels', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        place_id: hotel.place_id,
        name: hotel.name,
        address: hotel.address,
        latitude: hotel.latitude,
        longitude: hotel.longitude,
        search_postcode: nearbyCenter.value.postcode,
        locality: nearbyCenter.value.locality || null,
      }),
    })
    localMessage.value = saved.created
      ? `${saved.hotel.name} was added to Local Hotels with labeled simulated course rates and rooms.`
      : `${saved.hotel.name} is already saved locally; no duplicate was created.`
    await loadLocalHotels()
  } catch (err) {
    localError.value = err.message
  } finally {
    localSavingPlaceId.value = ''
  }
}

async function removeLocalHotel(hotel) {
  localError.value = ''
  localMessage.value = ''
  try {
    await request(`/local-hotels/${encodeURIComponent(hotel.place_id)}`, { method: 'DELETE' })
    localMessage.value = `${hotel.name} was removed from Local Hotels.`
    await loadLocalHotels()
  } catch (err) {
    localError.value = err.message
  }
}

async function askHotelAssistant() {
  if (chatLoading.value) return
  chatError.value = ''
  chatResult.value = null
  chatLoading.value = true
  try {
    chatResult.value = await request('/hotel-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: chatQuestion.value.trim() }),
    })
  } catch (err) {
    chatError.value = err.message
  } finally {
    chatLoading.value = false
  }
}

function chooseStay(stay) {
  selectedStay.value = stay
  message.value = ''
  error.value = ''
}

async function createBooking() {
  if (!selectedStay.value || !selectedUserId.value) return
  error.value = ''
  message.value = ''
  try {
    const booking = await request('/bookings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: selectedUserId.value, trip_id: selectedStay.value.trip_id }),
    })
    historyUserId.value = selectedUserId.value
    message.value = `Booking ${booking.booking_id} was created for ${booking.display_name}.`
    await loadBookings()
  } catch (err) {
    error.value = err.message
  }
}

async function cancelBooking(booking) {
  error.value = ''
  message.value = ''
  try {
    await request(`/bookings/${booking.booking_id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'cancelled' }),
    })
    message.value = `Booking ${booking.booking_id} was cancelled and kept in history.`
    await loadBookings()
  } catch (err) {
    error.value = err.message
  }
}

async function deleteBooking(booking) {
  error.value = ''
  message.value = ''
  try {
    await request(`/bookings/${booking.booking_id}`, { method: 'DELETE' })
    message.value = `Booking ${booking.booking_id} was deleted.`
    await loadBookings()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(async () => {
  try {
    await loadUsers()
    await loadBookings()
    await loadLocalHotels()
  } catch (err) {
    error.value = err.message
  }
})
</script>

<template>
  <main class="app-shell">
    <header class="site-header">
      <div class="brand" aria-label="Expedia Lite travel search">
        <span class="brand-mark" aria-hidden="true">✦</span>
        <span>Expedia Lite</span>
      </div>
      <nav class="site-nav" aria-label="Travel categories">
        <span>Stays</span>
        <span>Trips</span>
        <span>Support</span>
      </nav>
      <span class="member-note">Member prices available</span>
    </header>

    <section class="hero" aria-labelledby="page-title">
      <div class="hero-copy">
        <p class="eyebrow">Plan your next escape</p>
        <h1 id="page-title">Find a stay you’ll love.</h1>
        <p>Search available stays, make a simulated booking, and review booking history.</p>
        <ol class="booking-steps" aria-label="Booking workflow">
          <li><span>1</span> Search a stay</li>
          <li><span>2</span> Choose a traveler</li>
          <li><span>3</span> Manage the booking</li>
        </ol>
      </div>

      <form class="search-form search-card" @submit.prevent="search">
        <div class="search-field">
          <label for="hotel-name">Where are you going?</label>
          <input id="hotel-name" v-model="hotelName" placeholder="Try Valley Trail Inn or Boston" required />
        </div>
        <button class="primary-button" :disabled="loading">{{ loading ? 'Searching…' : 'Search stays' }}</button>
      </form>
    </section>

    <section class="live-discovery content-card" aria-labelledby="nearby-hotels-heading">
      <div class="section-heading">
        <div>
          <p class="eyebrow tool-eyebrow">Live hotel discovery</p>
          <h2 id="nearby-hotels-heading">Explore nearby hotels on a map</h2>
          <p>Search a verified U.S. ZIP code. Results are provider locations within 5 km of the returned ZIP center.</p>
        </div>
      </div>
      <form class="nearby-form" @submit.prevent="searchNearbyHotels">
        <div class="nearby-input">
          <label for="nearby-zip-code">U.S. ZIP code</label>
          <input id="nearby-zip-code" v-model="nearbyZipCode" :disabled="nearbyLoading" inputmode="numeric" maxlength="5" placeholder="Try 16802" aria-describedby="nearby-help" />
          <span id="nearby-help">Five digits, including leading zeros.</span>
        </div>
        <button class="primary-button" :disabled="nearbyLoading" type="submit">{{ nearbyLoading ? 'Searching…' : 'Search nearby hotels' }}</button>
      </form>
      <p v-if="nearbyLoading" class="inline-feedback" aria-live="polite">Resolving the ZIP code and finding nearby hotels…</p>
      <p v-if="nearbyError" class="message error" role="alert">{{ nearbyError }}</p>
      <p v-if="nearbyNoResults" class="message" role="status">No nearby hotel locations were returned within 5 km of {{ centerLabel(nearbyCenter) }}. This search completed successfully.</p>

      <div v-if="nearbyHotels.length" class="nearby-results" aria-live="polite">
        <div class="nearby-results-heading">
          <h3>{{ nearbyHotels.length }} nearby hotel location{{ nearbyHotels.length === 1 ? '' : 's' }}</h3>
          <p>Search center: {{ centerLabel(nearbyCenter) }}. Provider coverage and fields can vary.</p>
        </div>
        <div class="nearby-layout">
          <div class="hotel-result-list" aria-label="Nearby hotel results">
            <article v-for="(hotel, index) in nearbyHotels" :key="hotel.place_id" class="hotel-result-item">
              <button :class="['hotel-result-card', { selected: hotel.place_id === selectedNearbyPlaceId }]" type="button" :aria-pressed="hotel.place_id === selectedNearbyPlaceId" @click="selectNearbyHotel(hotel.place_id)">
                <span class="result-number">{{ index + 1 }}</span>
                <span class="hotel-result-copy">
                  <strong>{{ hotel.name || 'Name not provided' }}</strong>
                  <span>{{ hotel.address || 'Address not provided' }}</span>
                  <small>{{ formatDistance(hotel.distance_meters) }}</small>
                </span>
              </button>
              <button class="small-button save-local-button" type="button" :disabled="Boolean(localSavingPlaceId)" @click="saveLocalHotel(hotel)">
                {{ localSavingPlaceId === hotel.place_id ? 'Saving…' : 'Add to Local' }}
              </button>
            </article>
          </div>
          <HotelMap :search-center="nearbyCenter" :hotels="nearbyHotels" :selected-place-id="selectedNearbyPlaceId" @select="selectNearbyHotel" />
        </div>
      </div>
    </section>

    <section class="local-library content-card" aria-labelledby="local-hotels-heading">
      <div class="section-heading">
        <p class="eyebrow tool-eyebrow">Local SQLite storage</p>
        <h2 id="local-hotels-heading">Local Hotels</h2>
        <p>Save a nearby provider location once, then use it for local-first lookup and the assistant. Nightly rates and room counts below are simulated course data—not live inventory.</p>
      </div>
      <form class="local-search-form" @submit.prevent="loadLocalHotels">
        <div class="local-query-input">
          <label for="local-hotel-query">Search saved hotels</label>
          <input id="local-hotel-query" v-model="localQuery" :disabled="localLoading" placeholder="Name, location, or ZIP" />
        </div>
        <button class="secondary-button" :disabled="localLoading" type="submit">{{ localLoading ? 'Searching…' : 'Search Local' }}</button>
      </form>
      <p v-if="localError" class="message error" role="alert">{{ localError }}</p>
      <p v-if="localMessage" class="message success" role="status">{{ localMessage }}</p>
      <p v-if="!localLoading && !localHotels.length" class="message" role="status">No local hotels match this search. Add a location from the nearby-hotel results to create local course data.</p>
      <div v-if="localHotels.length" class="local-hotel-grid" aria-live="polite">
        <article v-for="hotel in localHotels" :key="hotel.place_id" class="local-hotel-card">
          <div class="local-hotel-heading">
            <div>
              <h3>{{ hotel.name }}</h3>
              <p>{{ hotel.address }}</p>
              <small>Saved from {{ hotel.search_postcode }}<span v-if="hotel.locality"> · {{ hotel.locality }}</span></small>
            </div>
            <button class="small-button delete-button" type="button" @click="removeLocalHotel(hotel)">Remove</button>
          </div>
          <p class="simulated-label">Simulated course data: nightly rates and rooms for October 10–16, 2026.</p>
          <ul class="demo-night-list">
            <li v-for="night in hotel.demo_nights" :key="night.stay_date">{{ demoNightLabel(night) }}</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="assistant-panel content-card" aria-labelledby="assistant-heading">
      <div class="section-heading">
        <p class="eyebrow tool-eyebrow">Grounded local assistant</p>
        <h2 id="assistant-heading">Ask about saved hotels</h2>
        <p>The assistant plans a checked read-only SQLite query, retrieves matching local records, then explains only those records. It cannot make a booking or change saved data.</p>
      </div>
      <form class="assistant-form" @submit.prevent="askHotelAssistant">
        <label for="hotel-question">Hotel question</label>
        <textarea id="hotel-question" v-model="chatQuestion" :disabled="chatLoading" maxlength="600" required></textarea>
        <button class="primary-button" :disabled="chatLoading" type="submit">{{ chatLoading ? 'Checking local hotels…' : 'Ask local assistant' }}</button>
      </form>
      <p v-if="chatLoading" class="inline-feedback" aria-live="polite">The assistant is proposing a safe query, checking local records, and grounding an answer…</p>
      <p v-if="chatError" class="message error" role="alert">{{ chatError }}</p>
      <div v-if="chatResult" class="chat-result" aria-live="polite">
        <p class="chat-question"><strong>Your question:</strong> {{ chatResult.question }}</p>
        <div class="chat-answer">
          <h3>Grounded answer</h3>
          <p>{{ chatResult.answer }}</p>
          <small>Rates and availability, if shown, are simulated course data.</small>
        </div>
        <details open>
          <summary>1. Proposed checked SQL</summary>
          <pre>{{ chatResult.proposed_sql }}<span v-if="chatResult.parameters.length">\nParameters: {{ JSON.stringify(chatResult.parameters) }}</span></pre>
        </details>
        <details open>
          <summary>2. Retrieved local records ({{ chatResult.records.length }})</summary>
          <p v-if="!chatResult.records.length" class="no-records">No local records matched this checked query.</p>
          <pre v-else>{{ JSON.stringify(chatResult.records, null, 2) }}</pre>
        </details>
      </div>
    </section>

    <section class="zip-panel travel-tool" aria-labelledby="zip-demo-heading">
      <div>
        <p class="eyebrow tool-eyebrow">Travel tool</p>
        <h2 id="zip-demo-heading">U.S. ZIP lookup</h2>
        <p>Enter any valid five-digit U.S. ZIP code to look up its location through the secure backend. The example starts with 16802.</p>
      </div>
      <form class="zip-form" @submit.prevent="lookupZip">
        <div class="zip-input">
          <label for="zip-code">Enter a ZIP code</label>
          <input id="zip-code" v-model="zipCode" :disabled="zipLoading" inputmode="numeric" maxlength="5" pattern="[0-9]{5}" placeholder="16802" required />
        </div>
        <button class="primary-button" :disabled="zipLoading" type="submit">{{ zipLoading ? 'Looking up ZIP…' : 'Look up ZIP' }}</button>
      </form>
      <p v-if="zipLoading" class="inline-feedback" aria-live="polite">Looking up ZIP {{ zipCode || '…' }}…</p>
      <p v-if="zipError" class="message error" role="alert">{{ zipError }}</p>
      <div v-if="zipLocation" class="zip-table-wrap" aria-live="polite">
        <table class="zip-result-table">
          <thead><tr><th>Postcode</th><th>Country code</th><th>Locality</th><th>Latitude</th><th>Longitude</th></tr></thead>
          <tbody><tr><td>{{ zipLocation.postcode }}</td><td>{{ zipLocation.country_code }}</td><td>{{ zipLocation.locality || '—' }}</td><td>{{ zipLocation.latitude }}</td><td>{{ zipLocation.longitude }}</td></tr></tbody>
        </table>
      </div>
    </section>

    <section class="feedback-area" aria-live="polite">
      <p v-if="error" class="message error">{{ error }}</p>
      <p v-if="message" class="message success">{{ message }}</p>
      <p v-if="searched && !loading && !results.length && !error" class="message">No hotel stays match “{{ hotelName }}”. Try another hotel name or city.</p>
    </section>

    <section v-if="results.length" class="result-section content-card">
      <h2>Matching hotel stays</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Trip ID</th><th>Hotel</th><th>City</th><th>Stay</th><th>Check-in</th><th>Check-out</th><th>Nights</th><th>Nightly rate</th><th>Estimated stay price</th><th>Action</th></tr></thead>
          <tbody><tr v-for="stay in results" :key="stay.trip_id"><td>{{ stay.trip_id }}</td><td>{{ stay.hotel_name }}</td><td>{{ stay.city }}, {{ stay.state }}</td><td>{{ stay.trip_name }}</td><td>{{ formatDate(stay.check_in) }}</td><td>{{ formatDate(stay.check_out) }}</td><td>{{ stay.nights }}</td><td>{{ formatMoney(stay.nightly_rate) }}</td><td>{{ formatMoney(stay.stay_price) }}</td><td><button class="small-button primary-button" type="button" :aria-label="`Book ${stay.trip_name} at ${stay.hotel_name}`" @click="chooseStay(stay)">Book</button></td></tr></tbody>
        </table>
      </div>
    </section>

    <section v-if="selectedStay" class="booking-card">
      <h2>Choose traveler and book</h2>
      <p class="booking-summary"><strong>{{ selectedStay.trip_name }}</strong> at {{ selectedStay.hotel_name }} <span>{{ selectedStay.trip_id }}</span></p>
      <form class="booking-form" @submit.prevent="createBooking">
        <label for="traveler">Traveler</label>
        <select id="traveler" v-model="selectedUserId" required>
          <option v-for="user in users" :key="user.user_id" :value="user.user_id">{{ user.display_name }}</option>
        </select>
        <button class="primary-button" type="submit">Create booking</button>
      </form>
    </section>

    <section class="history-section content-card">
      <h2>Booking history</h2>
      <p class="section-description">Review a booking, cancel it while keeping the record, or delete a test booking.</p>
      <form class="history-form" @submit.prevent="loadBookings">
        <label for="history-traveler">Traveler</label>
        <select id="history-traveler" v-model="historyUserId">
          <option value="">All travelers</option>
          <option v-for="user in users" :key="user.user_id" :value="user.user_id">{{ user.display_name }}</option>
        </select>
        <button class="secondary-button" :disabled="loadingHistory">{{ loadingHistory ? 'Loading…' : 'Show history' }}</button>
      </form>
      <p v-if="!loadingHistory && !bookings.length" class="message">No bookings match this history selection.</p>
      <div v-if="bookings.length" class="table-wrap">
        <table>
          <thead><tr><th>Booking ID</th><th>Traveler</th><th>Hotel stay</th><th>Booked on</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody><tr v-for="booking in bookings" :key="booking.booking_id"><td>{{ booking.booking_id }}</td><td>{{ booking.display_name }}</td><td>{{ booking.trip_name }} at {{ booking.hotel_name }}</td><td>{{ formatDate(booking.booked_on) }}</td><td><span :class="['status-pill', booking.status]">{{ booking.status }}</span></td><td class="actions"><button v-if="booking.status === 'confirmed'" class="small-button cancel-button" type="button" @click="cancelBooking(booking)">Cancel</button><button class="small-button delete-button" type="button" @click="deleteBooking(booking)">Delete</button></td></tr></tbody>
        </table>
      </div>
    </section>
  </main>
</template>
