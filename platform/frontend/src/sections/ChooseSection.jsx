import { useGSAP } from "@gsap/react";
import gsap from "gsap/all";
import { useMediaQuery } from "react-responsive";
import { chooseLinesLG, chooseLinesSM } from "../constants/welcome";

const ChooseSection = ({ onOpenDashboard }) => {
    const isMobile = useMediaQuery({ query: "(max-width:768px)" });
    const chooseLines = isMobile ? chooseLinesSM : chooseLinesLG;

    useGSAP(() => {
        const lines = gsap.utils.toArray(".choose-title-clip");

        const tl = gsap.timeline({
            scrollTrigger: {
                trigger: ".choose-section",
                start: "top 75%",
                end: "bottom 100%",
                scrub: true,
            },
        });

        tl.from(".choose-subtitle", {
            yPercent: 100,
            opacity: 0,
            ease: "power1.inOut",
        });

        if (!isMobile) {
            tl.fromTo(
                ".title-part",
                { height: "10vh" },
                { height: `${isMobile ? "22vh" : "50vh"}`, ease: "none" }
            );
        }

        tl.to(
            lines,
            {
                clipPath: "inset(0% 0% 0% 0%)",
                ease: "none",
                stagger: 0.2,
                duration: 1,
            },
            "<"
        );

        if (!isMobile) {
            tl.from(
                ".choose-sec",
                {
                    yPercent: 100,
                    duration: 1,
                },
                "<"
            );
        }
    });

    return (
        <section className="choose-section w-full h-dvh p-8 pt-10">
            <p className="text-[.7rem] text-[#eae5dd] choose-subtitle">
                Discover ZeroTrace<span>®</span> Capabilities
            </p>
            <div className="lg:mt-10 mt-7 title-part origin-bottom">
                {chooseLines.map((line, index) => (
                    <h2
                        key={index}
                        className="choose-heading text-[#f4efe7] lg:text-[9.5rem] text-[3rem] leading-[0.9] font-medium tracking-tighter"
                    >
                        <span
                            className={`choose-title-break ${index === 1 ? "lg:pb-3 pb-2" : ""}`}
                        >
                            {line}
                            <span
                                className={`choose-title-clip ${index === 1 ? "lg:pb-3 pb-2" : ""}`}
                            >
                                {line}
                            </span>
                        </span>
                    </h2>
                ))}
            </div>
            <div className="choose-sec w-full flex lg:flex-row flex-col justify-center items-start gap-10 lg:mt-0">
                <div className="lg:w-1/2 w-full text-[#b1a696] lg:text-[2rem] text-[1rem] md:leading-[1.1] lg:mt-0 mt-8 lg:pr-16">
                    <p>
                        ZeroTrace offers two primary operational modes. Select secure data sanitization
                        for irreversible media erasure, or advanced forensic recovery for deep file carving
                        and evidence reconstruction. Each mode meets the highest defense standards.
                    </p>
                </div>
                <div className="lg:w-1/2 w-full">
                    <div className="lg:w-[30%] w-[60%]">
                        <p className="text-[.7rem] text-[#eae5dd]">
                            All ZeroTrace® operations—are built following these standards:
                        </p>
                    </div>
                    <div className="flex flex-1 flex-wrap justify-start items-start gap-2 mt-8">
                        <div className="border-[1px] border-[#b1a696] text-[#b1a696] lg:text-[2rem] px-[20px] py-[4px] rounded-full">
                            NIST 800-88
                        </div>
                        <div className="border-[1px] border-[#f4efe7] text-[#f4efe7] lg:text-[2rem] px-[20px] py-[4px] rounded-full">
                            DoD 5220.22-M
                        </div>
                        <div className="border-[1px] border-[#b1a696] text-[#b1a696] lg:text-[2rem] px-[20px] py-[4px] rounded-full">
                            ISO 27037
                        </div>
                        <div className="border-[1px] border-[#f4efe7] text-[#f4efe7] lg:text-[2rem] px-[20px] py-[4px] rounded-full">
                            Merkle Proof
                        </div>
                        <div className="border-[1px] border-[#b1a696] text-[#b1a696] lg:text-[2rem] px-[20px] py-[4px] rounded-full">
                            SHA-256
                        </div>
                        <div className="border-[1px] border-[#f4efe7] text-[#f4efe7] lg:text-[2rem] px-[20px] py-[4px] rounded-full">
                            Gutmann 35-Pass
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default ChooseSection;
