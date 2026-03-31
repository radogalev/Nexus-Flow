import './App.css'
import { Link } from 'react-router-dom'

function App() {

  return (
    <>
      <h1 className = "text-red-500">React typescript app</h1>
      <Link to="/login" className="text-blue-600 underline">
        Go to Login
      </Link>
    </>
  )
}

export default App
