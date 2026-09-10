<script setup>
import { ref } from 'vue'

const API = 'http://127.0.0.1:8000/api'
const hotelName = ref('')
const results = ref([])
const searched = ref(false)
const loading = ref(false)
const error = ref('')

function formatDate(value) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${value}T12:00:00`))
}

function formatMoney(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

async function search() {
  searched.value = true
  error.value = ''
  loading.value = true
  try {
    const response = await fetch(`${API}/search?hotel_name=${encodeURIComponent(hotelName.value)}`)
    if (!response.ok) throw new Error('The search service is unavailable. Please try again.')
    results.value = await response.json()
  } catch (err) {
    error.value = err.message
    results.value = []
  } finally {
    loading.value = false
  }
}

</script>

<template>
  <main class="page">
    <h1>Expedia Hotel Search</h1>
    <p>Search available stays by hotel name or city.</p>
    <form @submit.prevent="search">
      <label for="hotel-name">Hotel name or city</label>
      <input id="hotel-name" v-model="hotelName" placeholder="Try Valley Trail Inn or Boston" required />
      <button :disabled="loading">{{ loading ? 'Searching…' : 'Search' }}</button>
    </form>

    <section aria-live="polite">
      <p v-if="error" class="message error">{{ error }}</p>
      <p v-if="searched && !loading && !results.length && !error" class="message">No hotel stays match “{{ hotelName }}”. Try another hotel name or city.</p>
      <section v-if="results.length">
        <h2>Matching hotel stays</h2>
        <table>
          <thead><tr><th>Trip ID</th><th>Hotel</th><th>City</th><th>Stay</th><th>Check-in</th><th>Check-out</th><th>Nights</th><th>Nightly rate</th><th>Estimated stay price</th></tr></thead>
          <tbody><tr v-for="stay in results" :key="stay.trip_id"><td>{{ stay.trip_id }}</td><td>{{ stay.hotel_name }}</td><td>{{ stay.city }}, {{ stay.state }}</td><td>{{ stay.trip_name }}</td><td>{{ formatDate(stay.check_in) }}</td><td>{{ formatDate(stay.check_out) }}</td><td>{{ stay.nights }}</td><td>{{ formatMoney(stay.nightly_rate) }}</td><td>{{ formatMoney(stay.stay_price) }}</td></tr></tbody>
        </table>
      </section>
    </section>
  </main>
</template>
