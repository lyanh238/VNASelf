import { useState, useEffect, useRef } from 'react'
import './LampToggle.css'

const LampToggle = ({ isDarkMode, onToggle }) => {
  const [isLampOn, setIsLampOn] = useState(!isDarkMode)
  const [isPulling, setIsPulling] = useState(false)
  const [stringAngle, setStringAngle] = useState(0)
  const [lampSwing, setLampSwing] = useState(0)
  const lampRef = useRef(null)
  const stringRef = useRef(null)
  const animationRef = useRef(null)

  // Sync with theme changes
  useEffect(() => {
    setIsLampOn(!isDarkMode)
  }, [isDarkMode])

  // Physics simulation for lamp swing
  useEffect(() => {
    if (isPulling) {
      const startTime = Date.now()
      const duration = 800 // Animation duration in ms
      
      const animate = () => {
        const elapsed = Date.now() - startTime
        const progress = Math.min(elapsed / duration, 1)
        
        // Easing function for natural movement
        const easeOut = 1 - Math.pow(1 - progress, 3)
        
        // String pull animation
        const pullAngle = Math.sin(progress * Math.PI) * 15
        setStringAngle(pullAngle)
        
        // Lamp swing after string release
        if (progress > 0.3) {
          const swingIntensity = Math.sin((progress - 0.3) * Math.PI * 2) * 8 * (1 - progress)
          setLampSwing(swingIntensity)
        }
        
        if (progress < 1) {
          animationRef.current = requestAnimationFrame(animate)
        } else {
          setIsPulling(false)
          setStringAngle(0)
          setLampSwing(0)
        }
      }
      
      animationRef.current = requestAnimationFrame(animate)
    }
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [isPulling])

  const handleStringPull = () => {
    if (!isPulling) {
      setIsPulling(true)
      setIsLampOn(!isLampOn)
      onToggle()
    }
  }

  return (
    <div className="lamp-container">
      {/* Ceiling */}
      <div className="ceiling"></div>
      
      {/* Lamp with physics */}
      <div 
        className={`lamp ${isLampOn ? 'on' : 'off'}`}
        ref={lampRef}
        style={{
          transform: `rotate(${lampSwing}deg)`
        }}
      >
        {/* Glass bulb (upside down) */}
        <div className="glass-bulb">
          {/* Glass sphere */}
          <div className="glass-sphere">
            {/* Filament wire inside */}
            <div className="filament-wire">
              <div className="filament-coil"></div>
              <div className="filament-coil filament-coil-2"></div>
            </div>
            
            {/* Internal reflections */}
            <div className="glass-reflection"></div>
            <div className="glass-highlight"></div>
          </div>
          
          {/* Single wire connection to bulb */}
          <div className="bulb-wire-connection">
            <div className="wire-contact"></div>
          </div>
          
          {/* Bulb glow effect */}
          <div className="bulb-ambient-glow"></div>
        </div>
        
        {/* Single wire from bulb to string */}
        <div className="single-wire">
          <div className="wire-bend"></div>
        </div>
        
        {/* String - now at bottom */}
        <div 
          className="lamp-string"
          ref={stringRef}
          style={{
            transform: `rotate(${stringAngle}deg)`
          }}
        >
          <div 
            className="string-pull"
            onClick={handleStringPull}
            onMouseDown={(e) => e.preventDefault()}
          >
            <div className="string-knot"></div>
          </div>
        </div>
      </div>
      
      {/* Light effect */}
      <div 
        className={`light-effect ${isLampOn ? 'active' : ''}`}
        style={{
          opacity: isLampOn ? 0.8 : 0,
          transform: `translateX(${lampSwing * 2}px)`
        }}
      />
    </div>
  )
}

export default LampToggle
