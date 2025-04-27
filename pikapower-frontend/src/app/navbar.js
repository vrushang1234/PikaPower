import Image from "next/image";
import pikaLogo from "@/assets/pikachu_logo.png";
export default function Navbar() {
  return (
    <header className="navbar">
      <div className="pikaLogo-container">
        <Image src={pikaLogo} className="pikaLogo" fill />
      </div>
      &emsp;
      <h1>PIKAPOWER</h1>
    </header>
  );
}
