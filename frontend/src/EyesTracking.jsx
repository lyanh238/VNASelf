import { useState, useEffect, useRef } from 'react'

const EyesTracking = ({ inputRef }) => {
  const [eyePosition, setEyePosition] = useState({ x: 0, y: 0 })
  const [isBlinking, setIsBlinking] = useState(false)
  const eyesRef = useRef(null)

  // Hiệu ứng nháy mắt ngẫu nhiên
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setIsBlinking(true)
      setTimeout(() => setIsBlinking(false), 150)
    }, Math.random() * 3000 + 2000) // Nháy mắt mỗi 2-5 giây

    return () => clearInterval(blinkInterval)
  }, [])

  useEffect(() => {
    const updateEyePosition = (event) => {
      if (inputRef?.current && eyesRef?.current) {
        const inputRect = inputRef.current.getBoundingClientRect()
        const eyesRect = eyesRef.current.getBoundingClientRect()
        
        // Lấy vị trí con trỏ trong input
        let targetX, targetY
        
        if (event && event.type === 'mousemove') {
          targetX = event.clientX
          targetY = event.clientY
        } else {
          // Tính toán vị trí con trỏ dựa trên vị trí cuối của text
          const input = inputRef.current
          const textWidth = input.value.length * 8 // Ước tính chiều rộng text
          targetX = inputRect.left + Math.min(textWidth, inputRect.width - 20)
          targetY = inputRect.top + inputRect.height / 2
        }
        
        // Tính toán góc nhìn từ mắt đến vị trí mục tiêu
        const eyesCenterX = eyesRect.left + eyesRect.width / 2
        const eyesCenterY = eyesRect.top + eyesRect.height / 2
        
        const deltaX = targetX - eyesCenterX
        const deltaY = targetY - eyesCenterY
        
        // Giới hạn chuyển động của con ngươi trong mắt
        const maxDistance = 6 // Khoảng cách tối đa con ngươi có thể di chuyển
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
        const limitedDistance = Math.min(distance, maxDistance)
        
        const angle = Math.atan2(deltaY, deltaX)
        const newX = Math.cos(angle) * limitedDistance
        const newY = Math.sin(angle) * limitedDistance
        
        setEyePosition({ x: newX, y: newY })
      }
    }

    // Cập nhật vị trí mắt khi input thay đổi
    if (inputRef?.current) {
      const input = inputRef.current
      input.addEventListener('input', updateEyePosition)
      input.addEventListener('focus', updateEyePosition)
      input.addEventListener('mousemove', updateEyePosition)
      input.addEventListener('blur', () => setEyePosition({ x: 0, y: 0 }))
      
      return () => {
        input.removeEventListener('input', updateEyePosition)
        input.removeEventListener('focus', updateEyePosition)
        input.removeEventListener('mousemove', updateEyePosition)
        input.removeEventListener('blur', () => setEyePosition({ x: 0, y: 0 }))
      }
    }
  }, [inputRef])

  return (
    <div ref={eyesRef} className="eyes-container">
      <svg width="64" height="64" viewBox="0 0 64 64" style={{ filter: 'drop-shadow(0 4px 12px rgba(217, 119, 6, 0.3))' }}>
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#56cee6ff" />
            <stop offset="100%" stopColor="#55b4ebff" />
          </linearGradient>
          <radialGradient id="pupilGradient" cx="30%" cy="30%">
            <stop offset="0%" stopColor="#1a1a1a" />
            <stop offset="100%" stopColor="#000000" />
          </radialGradient>
        </defs>
        
        {/* Mắt trái */}
        <g className={`eye left-eye ${isBlinking ? 'blinking' : ''}`}>
          <circle cx="20" cy="32" r="12" fill="white" stroke="url(#gradient)" strokeWidth="2"/>
          {!isBlinking && (
            <>
              <circle 
                cx={20 + eyePosition.x} 
                cy={32 + eyePosition.y} 
                r="6" 
                fill="url(#pupilGradient)"
                className="pupil"
              />
              {/* Highlight trong con ngươi */}
              <circle 
                cx={20 + eyePosition.x - 1.5} 
                cy={32 + eyePosition.y - 1.5} 
                r="1.5" 
                fill="white"
                opacity="0.8"
              />
            </>
          )}
        </g>
        
        {/* Mắt phải */}
        <g className={`eye right-eye ${isBlinking ? 'blinking' : ''}`}>
          <circle cx="44" cy="32" r="12" fill="white" stroke="url(#gradient)" strokeWidth="2"/>
          {!isBlinking && (
            <>
              <circle 
                cx={44 + eyePosition.x} 
                cy={32 + eyePosition.y} 
                r="6" 
                fill="url(#pupilGradient)"
                className="pupil"
              />
              {/* Highlight trong con ngươi */}
              <circle 
                cx={44 + eyePosition.x - 1.5} 
                cy={32 + eyePosition.y - 1.5} 
                r="1.5" 
                fill="white"
                opacity="0.8"
              />
            </>
          )}
        </g>
      </svg>
    </div>
  )
}

export default EyesTracking
