import gsap, { ScrollTrigger } from "gsap/all";
import { useGSAP } from "@gsap/react";
import { useState } from "react";

const StickyColsSection = () => {
    const [reveal, setReveal] = useState(false);

    useGSAP(() => {
        gsap.registerPlugin(ScrollTrigger);

        // Initial states
        gsap.set(".col-3 .col-content-wrapper", { opacity: 1, y: 0 });
        gsap.set(".col-3 .col-content-wrapper-2", { opacity: 0, y: 30, pointerEvents: "none" });

        const tl = gsap.timeline({
            scrollTrigger: {
                trigger: ".sticky-cols",
                start: "top 20%",
                end: "+=90%",
                pin: true,
                scrub: 1,
            },
        });

        tl.add(() => setReveal(false));

        // PHASE 1: Reveal col-2 & col-3, hide col-1
        tl.to(".col-1", { opacity: 0, scale: 0.8, duration: 0.8 })
            .to(".col-2", { x: "0%", duration: 0.8 }, "<")
            .to(".col-3", { y: "0%", duration: 0.8 }, "<")
            .to(".col-img-1 img", { scale: 1, duration: 0.8 }, "<")
            .to(
                ".col-img-2",
                {
                    clipPath: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
                    duration: 0.8,
                },
                "<"
            )
            .to(".col-img-2 img", { scale: 1.6, duration: 0.8 }, "<");

        tl.add(() => setReveal(false));
        tl.add(() => setReveal(true));

        // PHASE 2: Crossfade col-3 text from wrapper-1 to wrapper-2, and bring in col-4
        tl.to(".col-2", { opacity: 0, scale: 0.8, duration: 0.8 })
            .to(".col-3 .col-content-wrapper", { opacity: 0, y: -30, duration: 0.8 }, "<")
            .to(".col-3", { x: "0%", duration: 0.8 }, "-=0.8")
            .to(".col-4", { y: "0%", duration: 0.8 }, "<")
            .to(".col-3 .col-content-wrapper-2", { opacity: 1, y: 0, pointerEvents: "auto", duration: 0.8 }, "<");

        return () => {
            ScrollTrigger.getAll().forEach((st) => st.kill());
            tl.kill();
        };
    });

    return (
        <section className="sticky-cols w-screen h-dvh overflow-hidden bg-[#181717] lg:mb-20">
            <div className="sticky-cols-wrapper relative w-full h-screen">
                {/* Col 1: Text Content */}
                <div className="col col-1">
                    <div className="col-content">
                        <div className="col-content-wrapper">
                            <h2 className="text-2xl text-[#b1a696] font-bold leading-auto">
                                Certified data
                                <br />
                                sanitization—with
                                <br />
                                NIST SP 800-88
                                <br />
                                compliance
                            </h2>
                            <div className="col-content-para flex items-center gap-4 justify-between">
                                <div className="flex items-center gap-0 justify-center">
                                    <h3 className="border-1 px-3 py-1 rounded-full text-[#aaa091]">
                                        1
                                    </h3>
                                    <h3 className="border-1 px-3 py-1 rounded-full text-[#524e4b]">
                                        3
                                    </h3>
                                </div>
                                <p
                                    className={`text-[12px] font-medium ${!reveal ? "mr-6" : "mr-0"}`}
                                >
                                    Multi-pass overwrite with zero residual
                                    <br />
                                    magnetization verification on every sector.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Col 2: Images */}
                <div className="col col-2">
                    <div className="col-img col-img-1">
                        <div className="col-img-wrapper">
                            <img
                                src="/col-img-1.webp"
                                alt="Forensic analysis workstation"
                                loading="lazy"
                                decoding="async"
                                width="600"
                                height="800"
                                className="w-full h-full object-cover"
                                style={{ aspectRatio: "3 / 4" }}
                            />
                        </div>
                    </div>
                    <div className="col col-img-2 p-2">
                        <div className="col-img-wrapper">
                            <img
                                src="/col-img-2.webp"
                                alt="Secure server room cluster"
                                loading="lazy"
                                decoding="async"
                                width="600"
                                height="800"
                                className="w-full h-full object-cover"
                                style={{ aspectRatio: "3 / 4" }}
                            />
                        </div>
                    </div>
                </div>

                {/* Col 3: Text Content (second phase) */}
                <div className="col col-3">
                    <div className="col-content-wrapper">
                        <h2 className="text-2xl font-bold leading-auto">
                            Advanced file
                            <br />
                            carving—with deep
                            <br />
                            signature-based
                            <br />
                            recovery
                        </h2>
                        <div
                            className={`col-content-para flex items-center gap-4 justify-between ${reveal ? "ml-0" : "ml-6"}`}
                        >
                            <div className="flex items-center gap-0 justify-center">
                                <h3 className="border-1 px-3 py-1 rounded-full text-[#aaa091]">
                                    {reveal ? "3" : "2"}
                                </h3>
                                <h3 className="border-1 px-3 py-1 rounded-full text-[#524e4b]">
                                    3
                                </h3>
                            </div>
                            <p className="text-[12px] font-medium">
                                Recover deleted files from raw disk images
                                <br />
                                with bi-directional fragment reconstruction.
                            </p>
                        </div>
                    </div>
                    <div className="col-content-wrapper-2">
                        <h2 className="text-2xl font-bold leading-auto">
                            Merkle tree
                            <br />
                            integrity—tamper
                            <br />
                            evident hash
                            <br />
                            chain proof
                        </h2>
                        <div className="col-content-para flex items-center gap-4 justify-between">
                            <div className="flex items-center gap-0 justify-center">
                                <h3 className="border-1 px-3 py-1 rounded-full text-[#aaa091]">
                                    3
                                </h3>
                                <h3 className="border-1 px-3 py-1 rounded-full text-[#524e4b]">
                                    3
                                </h3>
                            </div>
                            <p
                                className={`text-[12px] font-medium ${!reveal ? "mr-0" : "mr-6"}`}
                            >
                                Every 4KB block independently hashed into
                                <br />a hierarchical Merkle tree for O(log N) proof.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Col 4: Image (third phase) */}
                <div className="col col-4">
                    <div className="col-img col-img-1">
                        <div className="col-img-wrapper">
                            <img
                                src="/col-img-3.webp"
                                alt="Digital forensic extraction workstation"
                                loading="lazy"
                                decoding="async"
                                width="600"
                                height="800"
                                className="w-full h-full object-cover"
                                style={{ aspectRatio: "3 / 4" }}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default StickyColsSection;
