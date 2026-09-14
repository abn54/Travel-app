<script setup>
import { onMounted, ref } from 'vue'

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
const error = ref('')
const message = ref('')

function formatDate(value) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${value}T12:00:00`))
}

function formatMoney(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
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
  } catch (err) {
    error.value = err.message
  }
})
</script>

<template>
  <main class="page">
    <h1>Expedia Hotel Search and Booking</h1>
    <p>Search available stays, make a simulated booking, and review booking history.</p>

    <form class="search-form" @submit.prevent="search">
      <label for="hotel-name">Hotel name or city</label>
      <input id="hotel-name" v-model="hotelName" placeholder="Try Valley Trail Inn or Boston" required />
      <button :disabled="loading">{{ loading ? 'Searching…' : 'Search' }}</button>
    </form>

    <section aria-live="polite">
      <p v-if="error" class="message error">{{ error }}</p>
      <p v-if="message" class="message success">{{ message }}</p>
      <p v-if="searched && !loading && !results.length && !error" class="message">No hotel stays match “{{ hotelName }}”. Try another hotel name or city.</p>
    </section>

    <section v-if="results.length" class="result-section">
      <h2>Matching hotel stays</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Trip ID</th><th>Hotel</th><th>City</th><th>Stay</th><th>Check-in</th><th>Check-out</th><th>Nights</th><th>Nightly rate</th><th>Estimated stay price</th><th>Action</th></tr></thead>
          <tbody><tr v-for="stay in results" :key="stay.trip_id"><td>{{ stay.trip_id }}</td><td>{{ stay.hotel_name }}</td><td>{{ stay.city }}, {{ stay.state }}</td><td>{{ stay.trip_name }}</td><td>{{ formatDate(stay.check_in) }}</td><td>{{ formatDate(stay.check_out) }}</td><td>{{ stay.nights }}</td><td>{{ formatMoney(stay.nightly_rate) }}</td><td>{{ formatMoney(stay.stay_price) }}</td><td><button class="small-button" type="button" @click="chooseStay(stay)">Book</button></td></tr></tbody>
        </table>
      </div>
    </section>

    <section v-if="selectedStay" class="panel">
      <h2>Book selected stay</h2>
      <p><strong>{{ selectedStay.trip_name }}</strong> at {{ selectedStay.hotel_name }} ({{ selectedStay.trip_id }}).</p>
      <form class="booking-form" @submit.prevent="createBooking">
        <label for="traveler">Traveler</label>
        <select id="traveler" v-model="selectedUserId" required>
          <option v-for="user in users" :key="user.user_id" :value="user.user_id">{{ user.display_name }}</option>
        </select>
        <button type="submit">Create booking</button>
      </form>
    </section>

    <section class="history-section">
      <h2>Booking history</h2>
      <form class="history-form" @submit.prevent="loadBookings">
        <label for="history-traveler">Traveler</label>
        <select id="history-traveler" v-model="historyUserId">
          <option value="">All travelers</option>
          <option v-for="user in users" :key="user.user_id" :value="user.user_id">{{ user.display_name }}</option>
        </select>
        <button :disabled="loadingHistory">{{ loadingHistory ? 'Loading…' : 'Show history' }}</button>
      </form>
      <p v-if="!loadingHistory && !bookings.length" class="message">No bookings match this history selection.</p>
      <div v-if="bookings.length" class="table-wrap">
        <table>
          <thead><tr><th>Booking ID</th><th>Traveler</th><th>Hotel stay</th><th>Booked on</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody><tr v-for="booking in bookings" :key="booking.booking_id"><td>{{ booking.booking_id }}</td><td>{{ booking.display_name }}</td><td>{{ booking.trip_name }} at {{ booking.hotel_name }}</td><td>{{ formatDate(booking.booked_on) }}</td><td>{{ booking.status }}</td><td class="actions"><button v-if="booking.status === 'confirmed'" class="small-button" type="button" @click="cancelBooking(booking)">Cancel</button><button class="small-button delete-button" type="button" @click="deleteBooking(booking)">Delete</button></td></tr></tbody>
        </table>
      </div>
    </section>
  </main>
</template>
