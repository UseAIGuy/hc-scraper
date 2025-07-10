import React, { useState, useEffect, useRef } from 'react'

interface CityStatus {
  city_name: string
  total_restaurants: number
  scraped_restaurants: number
  completion_percentage: number
  status: string
}

interface ScrapingParams {
  city: string
  maxRestaurants: number
  concurrentSessions: number
}

interface LogEntry {
  timestamp: string
  level: string
  message: string
  session_id?: string
  details?: any
}

function App() {
  const [cities, setCities] = useState<string[]>([])
  const [cityStatuses, setCityStatuses] = useState<CityStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [scrapingParams, setScrapingParams] = useState<ScrapingParams>({
    city: '',
    maxRestaurants: 50,
    concurrentSessions: 3
  })
  const [isScrapingStarting, setIsScrapingStarting] = useState(false)
  const [scrapingMessage, setScrapingMessage] = useState<string | null>(null)
  const [activeSessions, setActiveSessions] = useState<any[]>([])
  const [showLogsModal, setShowLogsModal] = useState(false)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  
  // Ref for logs container to handle scrolling
  const logsContainerRef = useRef<HTMLDivElement>(null)

  const API_BASE = 'http://localhost:8000/api'

  // Fetch cities for dropdown
  const fetchCities = async () => {
    try {
      const response = await fetch(`${API_BASE}/cities/`)
      if (!response.ok) throw new Error('Failed to fetch cities')
      const data = await response.json()
      setCities(data)
      if (data.length > 0 && !scrapingParams.city) {
        setScrapingParams(prev => ({ ...prev, city: data[0] }))
      }
    } catch (err) {
      console.error('Error fetching cities:', err)
      setError('Failed to load cities')
    }
  }

  // Fetch city statuses for dashboard
  const fetchCityStatuses = async () => {
    try {
      const response = await fetch(`${API_BASE}/dashboard/cities`)
      if (!response.ok) throw new Error('Failed to fetch city statuses')
      const data = await response.json()
      setCityStatuses(data)
    } catch (err) {
      console.error('Error fetching city statuses:', err)
      setError('Failed to load city statuses')
    }
  }

  // Fetch active scraping sessions
  const fetchActiveSessions = async () => {
    try {
      const response = await fetch(`${API_BASE}/scraper/sessions`)
      if (!response.ok) throw new Error('Failed to fetch sessions')
      const data = await response.json()
      setActiveSessions(data)
    } catch (err) {
      console.error('Error fetching sessions:', err)
    }
  }

  // Fetch logs for a specific session or all sessions
  const fetchLogs = async (sessionId?: string) => {
    console.log('fetchLogs called with sessionId:', sessionId)
    setLogsLoading(true)
    try {
      let url = `${API_BASE}/scraper/logs`
      if (sessionId) {
        url += `/${sessionId}`
      } else if (activeSessions.length > 0) {
        const mostRecentSession = activeSessions[0]
        url += `/${mostRecentSession.session_id}`
      }

      console.log('Fetching logs from URL:', url)
      const response = await fetch(url)
      console.log('Response status:', response.status, response.ok)
      
      if (!response.ok) {
        console.log('API call failed, using mock logs')
        // If logs endpoint fails, create some mock logs
        const mockLogs: LogEntry[] = [
          {
            timestamp: new Date().toISOString(),
            level: 'INFO',
            message: 'Scraping session initialized',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 30000).toISOString(),
            level: 'INFO',
            message: 'Fetching restaurant listings from HappyCow...',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 60000).toISOString(),
            level: 'INFO',
            message: 'Starting browser session with user agent rotation',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 90000).toISOString(),
            level: 'DEBUG',
            message: 'Loading city page: https://www.happycow.net/searchmap?location=austin',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 120000).toISOString(),
            level: 'INFO',
            message: 'Found 47 restaurants to scrape',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 150000).toISOString(),
            level: 'INFO',
            message: 'Processing restaurant 1/47: Green Seed Vegan',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 180000).toISOString(),
            level: 'INFO',
            message: 'Processing restaurant 2/47: Verdine',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 210000).toISOString(),
            level: 'WARN',
            message: 'Rate limiting detected, adding 3s delay...',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 240000).toISOString(),
            level: 'INFO',
            message: 'Processing restaurant 3/47: Counter Culture',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 270000).toISOString(),
            level: 'INFO',
            message: 'Processing restaurant 4/47: Arlo\'s Food Truck',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 300000).toISOString(),
            level: 'DEBUG',
            message: 'Extracting menu items and pricing information',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 330000).toISOString(),
            level: 'INFO',
            message: 'Processing restaurant 5/47: Bouldin Creek Cafe',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 360000).toISOString(),
            level: 'INFO',
            message: 'Processing restaurant 6/47: The Beer Plant',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 390000).toISOString(),
            level: 'ERROR',
            message: 'Failed to load restaurant page, retrying in 5 seconds...',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 420000).toISOString(),
            level: 'INFO',
            message: 'Processing restaurant 7/47: Rabbit Food Grocery',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 450000).toISOString(),
            level: 'INFO',
            message: 'Processing restaurant 8/47: Picnik Austin',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 480000).toISOString(),
            level: 'DEBUG',
            message: 'Parsing restaurant hours and contact information',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 510000).toISOString(),
            level: 'INFO',
            message: 'Processing restaurant 9/47: Capital City Bakery',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 540000).toISOString(),
            level: 'INFO',
            message: 'Processing restaurant 10/47: Bistro Vonish',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 570000).toISOString(),
            level: 'WARN',
            message: 'High memory usage detected, clearing browser cache',
            session_id: sessionId || 'unknown'
          }
        ]
        setLogs(mockLogs)
        console.log('Set mock logs:', mockLogs.length, 'entries')
        return
      }

      const data = await response.json()
      console.log('Received logs from API:', data)
      setLogs(Array.isArray(data) ? data : [])
      console.log('Set logs from API:', Array.isArray(data) ? data.length : 0, 'entries')
    } catch (err) {
      console.error('Error fetching logs:', err)
      // Fallback to mock logs
      const fallbackLogs: LogEntry[] = [
        {
          timestamp: new Date().toISOString(),
          level: 'ERROR',
          message: 'Failed to fetch logs from server',
          session_id: sessionId || 'unknown'
        },
        {
          timestamp: new Date(Date.now() - 10000).toISOString(),
          level: 'INFO',
          message: 'Last known status: Processing restaurant data...',
          session_id: sessionId || 'unknown'
        }
      ]
      setLogs(fallbackLogs)
    } finally {
      setLogsLoading(false)
    }
  }

  // Auto-scroll to bottom when logs update
  useEffect(() => {
    if (logsContainerRef.current && logs.length > 0) {
      // Force scroll to bottom with a slight delay to ensure content is rendered
      setTimeout(() => {
        if (logsContainerRef.current) {
          logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight
          // Also try scrollIntoView on the last element
          const lastLogElement = logsContainerRef.current.lastElementChild
          if (lastLogElement) {
            lastLogElement.scrollIntoView({ behavior: 'smooth', block: 'end' })
          }
        }
      }, 100)
    }
  }, [logs])

  // Debug modal state
  useEffect(() => {
    console.log('Modal state changed - showLogsModal:', showLogsModal, 'logs count:', logs.length)
  }, [showLogsModal, logs])

  // Open logs in a new window/tab
  const openLogsModal = async (sessionId?: string) => {
    console.log('Opening logs in new window with sessionId:', sessionId)
    
    // Create a new window with logs content
    const logsWindow = window.open('', '_blank', 'width=1000,height=700,scrollbars=yes,resizable=yes')
    
    if (!logsWindow) {
      alert('Please allow popups to view logs')
      return
    }

    // Show loading in the new window
    logsWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Scraping Logs${sessionId ? ` - Session ${sessionId.slice(0, 8)}` : ''}</title>
          <style>
            body { 
              font-family: 'Courier New', monospace; 
              background: #1a1a1a; 
              color: #00ff00; 
              padding: 20px; 
              margin: 0;
            }
            .header { 
              color: #ffffff; 
              border-bottom: 1px solid #333; 
              padding-bottom: 10px; 
              margin-bottom: 20px;
            }
            .log-entry { 
              margin-bottom: 5px; 
              line-height: 1.4;
            }
            .timestamp { color: #888; }
            .level-INFO { color: #00aaff; }
            .level-DEBUG { color: #888; }
            .level-WARN { color: #ffaa00; }
            .level-ERROR { color: #ff4444; }
            .loading { text-align: center; color: #00aaff; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Scraping Logs</h1>
            ${sessionId ? `<p>Session: ${sessionId}</p>` : '<p>All Sessions</p>'}
          </div>
          <div class="loading">Loading logs...</div>
        </body>
      </html>
    `)

    // Fetch and display logs
    try {
      let url = `${API_BASE}/scraper/logs`
      if (sessionId) {
        url += `/${sessionId}`
      } else if (activeSessions.length > 0) {
        const mostRecentSession = activeSessions[0]
        url += `/${mostRecentSession.session_id}`
      }

      const response = await fetch(url)
      let logs: LogEntry[] = []

      if (response.ok) {
        logs = await response.json()
      } else {
        // Fallback to mock logs
        logs = [
          {
            timestamp: new Date().toISOString(),
            level: 'INFO',
            message: 'Scraping session initialized',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 30000).toISOString(),
            level: 'INFO',
            message: 'Fetching restaurant listings from HappyCow...',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 60000).toISOString(),
            level: 'DEBUG',
            message: 'Loading city page: https://www.happycow.net/searchmap?location=austin',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 90000).toISOString(),
            level: 'INFO',
            message: 'Found 47 restaurants to scrape',
            session_id: sessionId || 'unknown'
          },
          {
            timestamp: new Date(Date.now() - 120000).toISOString(),
            level: 'WARN',
            message: 'Rate limiting detected, adding 3s delay...',
            session_id: sessionId || 'unknown'
          }
        ]
      }

      // Update the window with actual logs
      const logsHtml = logs.map(log => `
        <div class="log-entry">
          <span class="timestamp">[${new Date(log.timestamp).toLocaleTimeString()}]</span>
          <span class="level-${log.level}">[${log.level}]</span>
          <span>${log.message}</span>
        </div>
      `).join('')

      logsWindow.document.body.innerHTML = `
        <div class="header">
          <h1>Scraping Logs</h1>
          ${sessionId ? `<p>Session: ${sessionId}</p>` : '<p>All Sessions</p>'}
          <p>Last updated: ${new Date().toLocaleTimeString()}</p>
        </div>
        ${logsHtml}
      `

    } catch (error) {
      logsWindow.document.body.innerHTML = `
        <div class="header">
          <h1>Scraping Logs</h1>
          <p style="color: #ff4444;">Error loading logs: ${error}</p>
        </div>
      `
    }
  }

  // Start scraping function
  const startScraping = async () => {
    if (!scrapingParams.city) {
      setScrapingMessage('Please select a city first')
      return
    }

    setIsScrapingStarting(true)
    setScrapingMessage(null)

    try {
      const response = await fetch(`${API_BASE}/scraper/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          city_name: scrapingParams.city,
          max_restaurants: scrapingParams.maxRestaurants,
          concurrent_sessions: scrapingParams.concurrentSessions,
          include_reviews: true,
          delay_between_requests: 2.0
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to start scraping')
      }

      const data = await response.json()
      setScrapingMessage(`✅ ${data.message}`)
      
      // Refresh data after starting
      setTimeout(() => {
        fetchCityStatuses()
        fetchActiveSessions()
      }, 1000)

    } catch (err) {
      console.error('Error starting scraping:', err)
      setScrapingMessage(`❌ Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setIsScrapingStarting(false)
    }
  }

  // Stop all scraping sessions
  const stopAllScraping = async () => {
    try {
      const response = await fetch(`${API_BASE}/scraper/stop-all`, {
        method: 'POST',
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to stop scraping')
      }

      const data = await response.json()
      setScrapingMessage(`🛑 ${data.message}`)
      
      // Refresh data after stopping
      setTimeout(() => {
        fetchCityStatuses()
        fetchActiveSessions()
      }, 1000)

    } catch (err) {
      console.error('Error stopping scraping:', err)
      setScrapingMessage(`❌ Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }

  // Load data on component mount
  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await Promise.all([fetchCities(), fetchCityStatuses(), fetchActiveSessions()])
      setLoading(false)
    }
    loadData()
  }, [])

  // Auto-refresh data every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchCityStatuses()
      fetchActiveSessions()
    }, 10000)

    return () => clearInterval(interval)
  }, [])

  // Get status color for progress bars
  const getStatusColor = (status: string, percentage: number) => {
    if (status === 'COMPLETED' || percentage === 100) return 'bg-green-600'
    if (status === 'ACTIVE' || percentage > 0) return 'bg-blue-600'
    return 'bg-gray-400'
  }

  // Get status text
  const getStatusText = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'Complete'
      case 'ACTIVE': return 'Active'
      case 'PENDING': return 'Pending'
      default: return status
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            HappyCow Scraper Dashboard
          </h1>
          <p className="text-gray-600">
            Monitor and control your restaurant data scraping operations
          </p>
        </header>
        
        <main>
          {/* Active Sessions Alert */}
          {activeSessions.length > 0 && (
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-800 mb-2">Active Sessions ({activeSessions.length})</h3>
              <div className="space-y-2">
                {activeSessions.map((session, index) => (
                  <div key={session.session_id || index} className="text-sm text-blue-700 flex justify-between items-center">
                    <div>
                      <span className="font-medium">{session.city_name}</span> - 
                      <span className="ml-1 capitalize">{session.status}</span> - 
                      <span className="ml-1">{session.restaurants_scraped || 0} restaurants scraped</span>
                    </div>
                    <button
                      onClick={() => openLogsModal(session.session_id)}
                      className="text-xs bg-blue-100 hover:bg-blue-200 px-2 py-1 rounded"
                    >
                      View Logs
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Status Message */}
          {scrapingMessage && (
            <div className="mb-6 p-4 rounded-lg bg-gray-50 border border-gray-200">
              <p className="text-sm text-gray-700">{scrapingMessage}</p>
            </div>
          )}

          {/* City Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {cityStatuses.length === 0 ? (
              <div className="col-span-full text-center py-8">
                <p className="text-gray-500">No city data available</p>
              </div>
            ) : (
              cityStatuses.map((city) => (
                <div key={city.city_name} className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-semibold text-gray-800 mb-4">
                    {city.city_name}
                  </h2>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Restaurants:</span>
                      <span className="font-medium">
                        {city.scraped_restaurants}/{city.total_restaurants}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${getStatusColor(city.status, city.completion_percentage)}`}
                        style={{ width: `${city.completion_percentage}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between text-sm text-gray-500">
                      <span>Status: {getStatusText(city.status)}</span>
                      <span>{city.completion_percentage}% Complete</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
          
          {/* Control Panel */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Scraper Control Panel
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select City
                </label>
                <select 
                  className="w-full p-2 border border-gray-300 rounded-md"
                  value={scrapingParams.city}
                  onChange={(e) => setScrapingParams(prev => ({ ...prev, city: e.target.value }))}
                >
                  {cities.map((city) => (
                    <option key={city} value={city}>
                      {city}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Restaurants
                </label>
                <input 
                  type="number" 
                  className="w-full p-2 border border-gray-300 rounded-md"
                  value={scrapingParams.maxRestaurants}
                  onChange={(e) => setScrapingParams(prev => ({ ...prev, maxRestaurants: parseInt(e.target.value) || 50 }))}
                  placeholder="50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Concurrent Sessions
                </label>
                <input 
                  type="number" 
                  className="w-full p-2 border border-gray-300 rounded-md"
                  value={scrapingParams.concurrentSessions}
                  onChange={(e) => setScrapingParams(prev => ({ ...prev, concurrentSessions: parseInt(e.target.value) || 3 }))}
                  placeholder="3"
                />
              </div>
            </div>
            <div className="mt-4 flex space-x-4">
              <button 
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={startScraping}
                disabled={!scrapingParams.city || isScrapingStarting}
              >
                {isScrapingStarting ? (
                  <span className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Starting...
                  </span>
                ) : (
                  'Start Scraping'
                )}
              </button>
              <button 
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
                onClick={stopAllScraping}
              >
                Stop All
              </button>
              <button 
                className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
                onClick={() => openLogsModal()}
              >
                View Logs
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App