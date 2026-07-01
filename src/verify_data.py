from datetime import date
from sqlalchemy import select, func
from db.session import SessionLocal
from db.models import ParticipantOI, FIIDIICash, OptionChainSnapshot


def verify_today():
    today = date.today()
    print(f"\n{'='*60}")
    print(f"DATA VERIFICATION REPORT — {today}")
    print(f"{'='*60}")

    with SessionLocal() as db:

        # ---- Participant OI ----
        print("\n📊 PARTICIPANT OI (compare with NSE website)")
        print(f"{'Client Type':<12} {'Long OI':>12} {'Short OI':>12} {'Net OI':>12}")
        print("-" * 50)

        oi_rows = db.execute(
            select(ParticipantOI)
            .where(ParticipantOI.trade_date == today)
            .order_by(ParticipantOI.client_type)
        ).scalars().all()

        if not oi_rows:
            print("  ⚠ No participant OI data for today")
        else:
            for r in oi_rows:
                net = r.long_contracts - r.short_contracts
                print(f"{r.client_type:<12} {r.long_contracts:>12,} {r.short_contracts:>12,} {net:>+12,}")

        # ---- FII/DII Cash ----
        print("\n💵 FII/DII CASH ACTIVITY (compare with NSE website)")
        print(f"{'Entity':<8} {'Buy (Cr)':>12} {'Sell (Cr)':>12} {'Net (Cr)':>12}")
        print("-" * 46)

        cash_rows = db.execute(
            select(FIIDIICash)
            .where(FIIDIICash.trade_date == today)
            .order_by(FIIDIICash.entity_type)
        ).scalars().all()

        if not cash_rows:
            print("  ⚠ No FII/DII cash data for today")
        else:
            for r in cash_rows:
                net = float(r.buy_value) - float(r.sell_value)
                print(f"{r.entity_type:<8} {float(r.buy_value):>12,.2f} {float(r.sell_value):>12,.2f} {net:>+12,.2f}")

        # ---- Option Chain PCR ----
        print("\n📈 OPTION CHAIN — LATEST SNAPSHOT")

        latest_time = db.execute(
            select(func.max(OptionChainSnapshot.snapshot_time))
            .where(func.date(OptionChainSnapshot.snapshot_time) == today)
        ).scalar()

        if not latest_time:
            print("  ⚠ No option chain snapshots for today")
        else:
            result = db.execute(
                select(
                    func.sum(OptionChainSnapshot.ce_oi).label("total_ce"),
                    func.sum(OptionChainSnapshot.pe_oi).label("total_pe"),
                    func.count().label("strikes"),
                )
                .where(OptionChainSnapshot.snapshot_time == latest_time)
            ).one()

            pcr = round(result.total_pe / result.total_ce, 4) if result.total_ce else 0
            print(f"  Snapshot time : {latest_time.strftime('%H:%M:%S IST')}")
            print(f"  Strikes       : {result.strikes}")
            print(f"  Total CE OI   : {result.total_ce:,}")
            print(f"  Total PE OI   : {result.total_pe:,}")
            print(f"  PCR           : {pcr}")

        # ---- Snapshot count today ----
        print("\n⏱ SNAPSHOT HEALTH")
        snap_count = db.execute(
            select(func.count(func.distinct(OptionChainSnapshot.snapshot_time)))
            .where(func.date(OptionChainSnapshot.snapshot_time) == today)
        ).scalar()

        expected = 75  # 09:15 to 15:30 every 5 min = ~75 snapshots
        status = "✓" if snap_count >= expected * 0.9 else "⚠ GAPS DETECTED"
        print(f"  Snapshots today : {snap_count} / ~{expected} expected {status}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    verify_today()
