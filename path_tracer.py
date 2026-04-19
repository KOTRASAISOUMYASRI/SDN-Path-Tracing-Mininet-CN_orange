from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

# -----------------------------
# 🔴 FIREWALL RULE (FINAL)
# -----------------------------
BLOCKED_PAIRS = {
    ("00:00:00:00:00:01", "00:00:00:00:00:03"),  # h1 -> h3 blocked
}

# MAC → Switch mapping
mac_to_switch = {}


def _handle_PacketIn(event):
    packet = event.parsed
    dpid = event.dpid

    if not packet:
        return

    src = str(packet.src)
    dst = str(packet.dst)

    # -----------------------------
    # 🧹 IGNORE MULTICAST / DNS
    # -----------------------------
    if dst.startswith("33:33"):
        return

    # -----------------------------
    # 🔴 FIREWALL CHECK (DROP)
    # -----------------------------
    if (src, dst) in BLOCKED_PAIRS:
        log.info("🚫 BLOCKED: %s -> %s (Firewall Rule)", src, dst)
        return   # 🔥 STOP forwarding

    # -----------------------------
    # 📍 LEARN SOURCE LOCATION
    # -----------------------------
    mac_to_switch[src] = dpid

    log.info("PACKET IN: %s -> %s at Switch %s", src, dst, dpid)

    # -----------------------------
    # 🛣 PATH TRACE
    # -----------------------------
    if dst in mac_to_switch:
        log.info(
            "🛣 PATH TRACE: %s -> %s via Switch %s -> Switch %s",
            src, dst, mac_to_switch[src], mac_to_switch[dst]
        )

    # -----------------------------
    # 🔁 FORWARDING (FLOOD)
    # -----------------------------
    msg = of.ofp_packet_out()
    msg.data = event.ofp
    msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))

    event.connection.send(msg)


def launch():
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
    log.info("🔥 Path Tracing + Firewall Controller Started")
