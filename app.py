import json
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from svgpathtools import parse_path
from kafka_utilities import kafka_producer
import datetime


def main():
    if "button_id" not in st.session_state:
        st.session_state["button_id"] = ""
    if "color_to_label" not in st.session_state:
        st.session_state["color_to_label"] = {}
    PAGES = {
        "Basic example": full_app,
        "Get center coords of circles": center_circle_app,
        "Color-based image annotation": color_annotation_app,
        "Compute the length of drawn arcs": compute_arc_length,
    }
    page = st.sidebar.selectbox("Page:", options=list(PAGES.keys()))
    PAGES[page]()


def full_app():
    st.sidebar.header("Configuration")
    st.markdown(
        """
        Draw on the canvas, get the drawings back to Streamlit!
        * Configure canvas in the sidebar
        * In transform mode, double-click an object to remove it
        * In polygon mode, left-click to add a point, right-click to close the polygon, double-click to remove the latest point
        """
    )

    # Specify canvas parameters in application
    drawing_mode = st.sidebar.selectbox(
        "Drawing tool:",
        ("freedraw", "line", "rect", "circle", "transform", "polygon", "point"),
    )
    kafka_producer(
        request_dict={
            "timestamp": datetime.datetime.now().isoformat(),
            "message_type": "basic-example",
            "drawing_mode": drawing_mode,
        }
    )
    stroke_width = st.sidebar.slider("Stroke width: ", 1, 25, 3)
    kafka_producer(
        request_dict={
            "timestamp": datetime.datetime.now().isoformat(),
            "message_type": "basic-example",
            "stroke_width": stroke_width,
        }
    )
    if drawing_mode == "point":
        point_display_radius = st.sidebar.slider("Point display radius: ", 1, 25, 3)
        kafka_producer(
            request_dict={
                "timestamp": datetime.datetime.now().isoformat(),
                "message_type": "basic-example",
                "point_display_radius": point_display_radius,
            }
        )
    stroke_color = st.sidebar.color_picker("Stroke color hex: ")
    kafka_producer(
        request_dict={
            "timestamp": datetime.datetime.now().isoformat(),
            "message_type": "basic-example",
            "stroke_color": stroke_color,
        }
    )
    bg_color = st.sidebar.color_picker("Background color hex: ", "#eee")
    kafka_producer(
        request_dict={
            "timestamp": datetime.datetime.now().isoformat(),
            "message_type": "basic-example",
            "bg_color": bg_color,
        }
    )
    bg_image = st.sidebar.file_uploader("Background image:", type=["png", "jpg"])
    kafka_producer(
        request_dict={
            "timestamp": datetime.datetime.now().isoformat(),
            "message_type": "basic-example",
            "bg_image": bg_image,
        }
    )
    realtime_update = st.sidebar.checkbox("Update in realtime", True)
    kafka_producer(
        request_dict={
            "timestamp": datetime.datetime.now().isoformat(),
            "message_type": "basic-example",
            "realtime_update": realtime_update,
        }
    )

    # Create a canvas component
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color=bg_color,
        background_image=Image.open(bg_image) if bg_image else None,
        update_streamlit=realtime_update,
        height=500,
        drawing_mode=drawing_mode,
        point_display_radius=point_display_radius if drawing_mode == "point" else 0,
        display_toolbar=st.sidebar.checkbox("Display toolbar", True),
        key="full_app",
    )

    # Do something interesting with the image data and paths
    if canvas_result.image_data is not None:
        st.image(canvas_result.image_data)
    if canvas_result.json_data is not None:
        if canvas_result.json_data.get("objects"):
            # for each key in the json_data, we can get the value
            # and produce a message to the kafka topic
            for key in canvas_result.json_data["objects"][0].keys():
                if key == "path":
                    new_message = "new path drawn"
                else:
                    new_message = canvas_result.json_data["objects"][0].get(key)
                kafka_producer(
                    request_dict={
                        "timestamp": datetime.datetime.now().isoformat(),
                        "message_type": "basic-example",
                        key: new_message,
                    }
                )
        objects = pd.json_normalize(canvas_result.json_data["objects"])
        for col in objects.select_dtypes(include=["object"]).columns:
            objects[col] = objects[col].astype("str")
        st.dataframe(objects)


def center_circle_app():
    st.markdown(
        """
    Computation of center coordinates for circle drawings some understanding of Fabric.js coordinate system
    and play with some trigonometry.

    Coordinates are canvas-related to top-left of image, increasing x going down and y going right.

    ```
    center_x = left + radius * cos(angle * pi / 180)
    center_y = top + radius * sin(angle * pi / 180)
    ```
    """
    )
    bg_image = Image.open("img/dnd.jpeg")

    with open("saved_state.json", "r") as f:
        saved_state = json.load(f)

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.2)",  # Fixed fill color with some opacity
        stroke_width=5,
        stroke_color="black",
        background_image=bg_image,
        initial_drawing=(
            saved_state
            if st.sidebar.checkbox("Initialize with saved state", False)
            else None
        ),
        height=400,
        width=600,
        drawing_mode="circle",
        key="center_circle_app",
    )

    if canvas_result.json_data is not None:
        kafka_producer(
            request_dict={
                "timestamp": datetime.datetime.now().isoformat(),
                "message_type": "center-circle",
                "body": canvas_result.json_data["objects"],
            }
        )
        df = pd.json_normalize(canvas_result.json_data["objects"])
        if len(df) == 0:
            return
        df["center_x"] = df["left"] + df["radius"] * np.cos(df["angle"] * np.pi / 180)
        df["center_y"] = df["top"] + df["radius"] * np.sin(df["angle"] * np.pi / 180)

        st.subheader("List of circle drawings")
        for _, row in df.iterrows():
            st.markdown(
                f'Center coords: ({row["center_x"]:.2f}, {row["center_y"]:.2f}). Radius: {row["radius"]:.2f}'
            )
            kafka_producer(
                request_dict={
                    "timestamp": datetime.datetime.now().isoformat(),
                    "message_type": "center-circle",
                    "body": {
                        "center_x": row["center_x"],
                        "center_y": row["center_y"],
                        "radius": row["radius"],
                    },
                }
            )


def color_annotation_app():
    st.markdown(
        """
    Drawable Canvas doesn't provided out-of-the-box image annotation capabilities, but we can hack something with session state,
    by mapping a drawing fill color to a label.

    Annotate pedestrians, cars and traffic lights with this one, with any color/label you want 
    (though in a real app you should rather provide your own label and fills :smile:).

    If you really want advanced image annotation capabilities, you'd better check [Streamlit Label Studio](https://discuss.streamlit.io/t/new-component-streamlit-labelstudio-allows-you-to-embed-the-label-studio-annotation-frontend-into-your-application/9524)
    """
    )

    bg_image = Image.open("img/annotation.jpeg")
    label_color = (
        st.sidebar.color_picker("Annotation color: ", "#EA1010") + "77"
    )  # for alpha from 00 to FF
    kafka_producer(
        request_dict={
            "timestamp": datetime.datetime.now().isoformat(),
            "message_type": "color-annotation",
            "body": label_color,
        }
    )
    label = st.sidebar.text_input("Label", "Default")
    kafka_producer(
        request_dict={
            "timestamp": datetime.datetime.now().isoformat(),
            "message_type": "color-annotation",
            "body": label,
        }
    )
    mode = "transform" if st.sidebar.checkbox("Move ROIs", False) else "rect"
    kafka_producer(
        request_dict={
            "timestamp": datetime.datetime.now().isoformat(),
            "message_type": "color-annotation",
            "body": mode,
        }
    )

    canvas_result = st_canvas(
        fill_color=label_color,
        stroke_width=3,
        background_image=bg_image,
        height=320,
        width=512,
        drawing_mode=mode,
        key="color_annotation_app",
    )
    if canvas_result.json_data is not None:
        kafka_producer(
            request_dict={
                "timestamp": datetime.datetime.now().isoformat(),
                "message_type": "color-annotation",
                "body": canvas_result.json_data["objects"],
            }
        )
        df = pd.json_normalize(canvas_result.json_data["objects"])
        if len(df) == 0:
            return
        st.session_state["color_to_label"][label_color] = label
        df["label"] = df["fill"].map(st.session_state["color_to_label"])
        st.dataframe(df[["top", "left", "width", "height", "fill", "label"]])

    with st.expander("Color to label mapping"):
        st.json(st.session_state["color_to_label"])


def compute_arc_length():
    st.markdown(
        """
    Using an external SVG manipulation library like [svgpathtools](https://github.com/mathandy/svgpathtools)
    You can do some interesting things on drawn paths.
    In this example we compute the length of any drawn path.
    """
    )

    bg_image = Image.open("img/annotation.jpeg")

    canvas_result = st_canvas(
        stroke_color="yellow",
        stroke_width=3,
        background_image=bg_image,
        height=320,
        width=512,
        drawing_mode="freedraw",
        key="compute_arc_length",
    )
    if (
        canvas_result.json_data is not None
        and len(canvas_result.json_data["objects"]) != 0
    ):
        kafka_producer(
            request_dict={
                "timestamp": datetime.datetime.now().isoformat(),
                "message_type": "compute-arc-length",
                "body": canvas_result.json_data["objects"],
            }
        )
        df = pd.json_normalize(canvas_result.json_data["objects"])
        paths = df["path"].tolist()
        for ind, path in enumerate(paths):
            path = parse_path(" ".join([str(e) for line in path for e in line]))
            st.write(f"Path {ind} has length {path.length():.3f} pixels")
            kafka_producer(
                request_dict={
                    "timestamp": datetime.datetime.now().isoformat(),
                    "message_type": "compute-arc-length",
                    "body": {"path": path, "length": f"{path.length():.3f} pixels"},
                }
            )


if __name__ == "__main__":
    st.set_page_config(
        page_title="Streamlit Drawable Canvas Demo", page_icon=":pencil2:"
    )
    st.title("Drawable Canvas Demo")
    st.sidebar.subheader("Configuration")
    main()
