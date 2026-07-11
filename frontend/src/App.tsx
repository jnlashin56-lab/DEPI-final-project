import { useState, useEffect } from 'react'
import { Sparkles, MapPin, Users, Banknote, X, Ticket, Globe } from 'lucide-react'
import { recommendItinerary, chatBooking } from './api'
import type { ItineraryStop } from './api'
import './index.css'

function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [stops, setStops] = useState<ItineraryStop[]>([])
  const [error, setError] = useState('')
  const [lang, setLang] = useState<'en' | 'ar'>('en')

  // Booking Modal State
  const [bookingPlace, setBookingPlace] = useState<ItineraryStop | null>(null)
  const [chatMessages, setChatMessages] = useState<{role: 'bot'|'user', text: string}[]>([])
  const [chatInput, setChatInput] = useState('')
  const [bookingLoading, setBookingLoading] = useState(false)

  // Toggle RTL
  useEffect(() => {
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
  }, [lang])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    
    setLoading(true)
    setError('')
    setStops([])
    
    try {
      const data = await recommendItinerary(query)
      setStops(data.itinerary)
    } catch (err: any) {
      setError(err.message || (lang === 'ar' ? 'فشل جلب التوصيات. تأكد من تشغيل الخادم الخلفي.' : 'Failed to fetch recommendations. Is the backend running?'))
    } finally {
      setLoading(false)
    }
  }

  const openBooking = (place: ItineraryStop) => {
    setBookingPlace(place)
    const placeName = lang === 'ar' && place.name_ar ? place.name_ar : place.name
    const greeting = lang === 'ar' 
      ? `أهلاً! يمكنني مساعدتك في حجز تذاكر لـ ${placeName}. كم عدد الأشخاص، ومتى ترغبون في الزيارة؟`
      : `Hi! I can help you book tickets for ${placeName}. How many people are going, and what time would you like to visit?`
    
    setChatMessages([
      { role: 'bot', text: greeting }
    ])
  }

  const handleChatSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim() || bookingLoading) return

    const userMsg = chatInput
    setChatInput('')
    setChatMessages(prev => [...prev, { role: 'user', text: userMsg }])
    setBookingLoading(true)

    try {
      const historyStr = chatMessages.map(m => `${m.role === 'bot' ? 'Assistant' : 'User'}: ${m.text}`).join('\n')
      const fullContext = `Place ID: ${bookingPlace?.place_id}. Place: ${bookingPlace?.name}.\nChat History:\n${historyStr}\nUser: ${userMsg}`
      
      const response = await chatBooking(fullContext)
      setChatMessages(prev => [...prev, { 
        role: 'bot', 
        text: response.result?.message || (lang === 'ar' ? 'جاري معالجة طلبك...' : 'Processing your request...') 
      }])
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'bot', text: lang === 'ar' ? 'عذراً، حدث خطأ.' : 'Sorry, there was an error processing your booking.' }])
    } finally {
      setBookingLoading(false)
    }
  }

  return (
    <div className="app-container">
      <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem'}}>
        <button 
          onClick={() => setLang(lang === 'en' ? 'ar' : 'en')}
          style={{
            background: 'transparent', border: '1px solid var(--border-color)', 
            color: 'var(--text-primary)', padding: '0.5rem 1rem', borderRadius: '8px',
            display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer'
          }}
        >
          <Globe size={16} /> {lang === 'en' ? 'العربية' : 'English'}
        </button>
      </div>

      <header className="header">
        <h1 className="header-title">
          {lang === 'ar' ? 'اكتشف أسرار مصر' : 'Discover the Mysteries of Egypt'}
        </h1>
        <p className="header-subtitle">
          {lang === 'ar' 
            ? 'أخبرنا بما تريد رؤيته، وميزانيتك، ووقتك. سيقوم الذكاء الاصطناعي بتصميم مسار ثقافي خصيصاً لك.'
            : 'Tell us what you want to see, your budget, and your time. Our AI will craft a beautifully tailored cultural itinerary just for you.'}
        </p>
      </header>

      <form className="search-container" onSubmit={handleSearch}>
        <input 
          type="text" 
          className="search-input"
          placeholder={lang === 'ar' ? 'مثال: لدي 4 ساعات و 500 جنيه لرؤية المعابد...' : 'e.g., I have 4 hours and 500 EGP to see ancient temples in Luxor...'}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
          dir={lang === 'ar' && !query ? 'rtl' : 'auto'}
        />
        <button type="submit" className="search-button" disabled={loading || !query.trim()}>
          {loading ? <div className="spinner" /> : <><Sparkles size={18} /> {lang === 'ar' ? 'اكتشف' : 'Discover'}</>}
        </button>
      </form>

      {error && <div style={{color: '#f87171', textAlign: 'center', marginBottom: '2rem'}}>{error}</div>}

      {stops.length > 0 && (() => {
        const groupedStops = stops.reduce((acc, stop) => {
          const day = stop.day || 1;
          if (!acc[day]) acc[day] = [];
          acc[day].push(stop);
          return acc;
        }, {} as Record<number, ItineraryStop[]>);
        const hasMultipleDays = Object.keys(groupedStops).length > 1;

        return (
          <div className="itinerary-list">
            {Object.entries(groupedStops).map(([day, dayStops]) => (
              <div key={`day-${day}`} className="day-group">
                {hasMultipleDays && (
                  <h2 className="day-header">
                    {lang === 'ar' ? `اليوم ${day}` : `Day ${day}`}
                  </h2>
                )}
                {dayStops.map((stop, idx) => (
                  <div key={idx} className="stop-item glass-panel" style={{animationDelay: `${idx * 0.2}s`}}>
                    <div className="stop-number">{idx + 1}</div>
                    <div className="stop-content">
                      <div className="stop-header">
                        <div>
                          <h2 className="stop-title">{lang === 'ar' && stop.name_ar ? stop.name_ar : stop.name}</h2>
                          <span className="stop-category">{stop.category}</span>
                        </div>
                        <div className="stop-meta">
                          <span className="badge price">
                            <Banknote size={14} /> {stop.price_egp ? `${stop.price_egp} EGP` : (lang === 'ar' ? 'مجاني / متفاوت' : 'Free / Varies')}
                          </span>
                          <span className={`badge crowd-${stop.predicted_crowd}`}>
                            <Users size={14} /> {lang === 'ar' ? 'الازدحام:' : 'Crowd:'} {stop.predicted_crowd}
                          </span>
                        </div>
                      </div>
                      
                      <p className="story-text">"{stop.story}"</p>
                      
                      <button className="book-btn" onClick={() => openBooking(stop)}>
                        <Ticket size={16} /> {lang === 'ar' ? 'حجز التذاكر' : 'Book Tickets'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        );
      })()}

      {/* Booking Modal */}
      {bookingPlace && (
        <div className="modal-overlay" onClick={() => setBookingPlace(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setBookingPlace(null)} style={lang === 'ar' ? {left: '1rem', right: 'auto'} : {right: '1rem', left: 'auto'}}>
              <X size={24} />
            </button>
            <h3 style={{marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
              <MapPin size={20} color="var(--accent-primary)" /> {lang === 'ar' && bookingPlace.name_ar ? bookingPlace.name_ar : bookingPlace.name}
            </h3>
            
            <div className="chat-container">
              <div className="chat-messages">
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`chat-bubble ${msg.role}`}>
                    {msg.text}
                  </div>
                ))}
                {bookingLoading && (
                  <div className="chat-bubble bot" style={{opacity: 0.7}}>{lang === 'ar' ? 'يفكر...' : 'Thinking...'}</div>
                )}
              </div>
              <form className="chat-input-area" onSubmit={handleChatSend}>
                <input 
                  type="text" 
                  className="chat-input"
                  placeholder={lang === 'ar' ? "اكتب رسالتك..." : "Type your message..."}
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  disabled={bookingLoading}
                />
                <button type="submit" className="chat-send" disabled={bookingLoading || !chatInput.trim()}>
                  {lang === 'ar' ? 'إرسال' : 'Send'}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
